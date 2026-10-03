"""
Identity tracking and per-person cooldown manager.
"""
from dataclasses import dataclass, field
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from config import DEFAULT_COOLDOWN_SECONDS, RECOGNITION_COSINE_THRESHOLD
from src.face_engine import DetectedFace, FaceEngine


@dataclass
class TrackedIdentity:
    identity_id: str
    display_name: str
    is_enrolled: bool
    embedding: np.ndarray
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    last_greeted: float = 0.0
    greeting_count: int = 0


@dataclass
class TrackedFaceResult:
    detected_face: DetectedFace
    identity_id: str
    display_name: str
    is_enrolled: bool
    similarity_score: float
    should_greet: bool
    cooldown_remaining: float


class IdentityTracker:
    def __init__(
        self,
        face_engine: FaceEngine,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        cosine_threshold: float = RECOGNITION_COSINE_THRESHOLD,
    ):
        self.face_engine = face_engine
        self.cooldown_seconds = cooldown_seconds
        self.cosine_threshold = cosine_threshold

        # Tracked active identities in session {identity_id: TrackedIdentity}
        self.identities: Dict[str, TrackedIdentity] = {}
        self._next_visitor_id = 1

    def set_cooldown(self, seconds: float) -> None:
        """Update cooldown period in seconds."""
        self.cooldown_seconds = max(1.0, float(seconds))

    def _find_matching_identity(
        self, feature: np.ndarray
    ) -> Tuple[Optional[str], float]:
        """Find matching identity among active session identities."""
        best_id = None
        best_score = -1.0

        for id_key, identity in self.identities.items():
            score = self.face_engine.match_features(feature, identity.embedding)
            if score > best_score:
                best_score = score
                best_id = id_key

        if best_score >= self.cosine_threshold:
            return best_id, best_score
        return None, best_score

    def process_detected_faces(
        self, detected_faces: List[DetectedFace]
    ) -> List[TrackedFaceResult]:
        """Process detected faces, match identities, and evaluate greeting cooldowns."""
        now = time.time()
        results: List[TrackedFaceResult] = []

        for face in detected_faces:
            if face.feature is None:
                continue

            # 1. First check if it matches an enrolled known face from known_faces/
            enrolled_name, enrolled_score = self.face_engine.identify_face(face.feature)

            identity_id = None
            display_name = ""
            is_enrolled = False
            similarity = 0.0

            if enrolled_name is not None:
                # Matches known enrolled face
                identity_id = f"enrolled_{enrolled_name.lower().replace(' ', '_')}"
                display_name = enrolled_name
                is_enrolled = True
                similarity = enrolled_score

                if identity_id not in self.identities:
                    self.identities[identity_id] = TrackedIdentity(
                        identity_id=identity_id,
                        display_name=display_name,
                        is_enrolled=True,
                        embedding=face.feature,
                        first_seen=now,
                        last_seen=now,
                    )
            else:
                # 2. Check if it matches an existing session visitor
                matched_id, matched_score = self._find_matching_identity(face.feature)
                if matched_id is not None:
                    identity_id = matched_id
                    display_name = self.identities[matched_id].display_name
                    is_enrolled = self.identities[matched_id].is_enrolled
                    similarity = matched_score
                else:
                    # 3. New visitor - register dynamic ID
                    identity_id = f"visitor_{self._next_visitor_id}"
                    display_name = f"Human #{self._next_visitor_id}"
                    self._next_visitor_id += 1
                    is_enrolled = False
                    similarity = 1.0

                    self.identities[identity_id] = TrackedIdentity(
                        identity_id=identity_id,
                        display_name=display_name,
                        is_enrolled=False,
                        embedding=face.feature,
                        first_seen=now,
                        last_seen=now,
                    )

            # Update identity activity
            ident = self.identities[identity_id]
            ident.last_seen = now
            # Blend embedding slightly to adapt to lighting/angle variations
            ident.embedding = 0.9 * ident.embedding + 0.1 * face.feature

            # Check cooldown status
            time_since_greet = now - ident.last_greeted
            if ident.last_greeted == 0.0 or time_since_greet >= self.cooldown_seconds:
                should_greet = True
                cooldown_remaining = 0.0
            else:
                should_greet = False
                cooldown_remaining = max(0.0, self.cooldown_seconds - time_since_greet)

            results.append(
                TrackedFaceResult(
                    detected_face=face,
                    identity_id=identity_id,
                    display_name=display_name,
                    is_enrolled=is_enrolled,
                    similarity_score=similarity,
                    should_greet=should_greet,
                    cooldown_remaining=cooldown_remaining,
                )
            )

        return results

    def mark_greeted(self, identity_id: str) -> None:
        """Mark an identity as having just received an audio greeting."""
        if identity_id in self.identities:
            self.identities[identity_id].last_greeted = time.time()
            self.identities[identity_id].greeting_count += 1

    def reset_cooldown(self, identity_id: Optional[str] = None) -> None:
        """Reset cooldown for a specific identity or all identities."""
        if identity_id:
            if identity_id in self.identities:
                self.identities[identity_id].last_greeted = 0.0
        else:
            for ident in self.identities.values():
                ident.last_greeted = 0.0
