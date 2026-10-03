"""
Face Detection and Recognition engine powered by OpenCV YuNet and SFace.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

from config import (
    YUNET_MODEL_PATH,
    SFACE_MODEL_PATH,
    DETECTION_SCORE_THRESHOLD,
    DETECTION_NMS_THRESHOLD,
    DETECTION_TOP_K,
    RECOGNITION_COSINE_THRESHOLD,
)
from download_models import ensure_models


class DetectedFace:
    """Represents a detected face with bbox, landmarks, score, and embedding."""
    def __init__(self, raw_face: np.ndarray, feature: Optional[np.ndarray] = None):
        self.raw = raw_face
        # Bounding box [x, y, w, h]
        self.bbox = [int(v) for v in raw_face[0:4]]
        # 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner)
        self.landmarks = raw_face[4:14].reshape((5, 2)).astype(int)
        self.score = float(raw_face[14])
        self.feature = feature  # 1x128 embedding vector


class FaceEngine:
    def __init__(
        self,
        input_size: Tuple[int, int] = (640, 480),
        score_threshold: float = DETECTION_SCORE_THRESHOLD,
        nms_threshold: float = DETECTION_NMS_THRESHOLD,
        top_k: int = DETECTION_TOP_K,
        cosine_threshold: float = RECOGNITION_COSINE_THRESHOLD,
    ):
        ensure_models()

        self.input_size = input_size
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self.cosine_threshold = cosine_threshold

        # Initialize YuNet face detector
        self.detector = cv2.FaceDetectorYN.create(
            str(YUNET_MODEL_PATH),
            "",
            self.input_size,
            score_threshold=self.score_threshold,
            nms_threshold=self.nms_threshold,
            top_k=self.top_k,
        )

        # Initialize SFace face recognizer
        self.recognizer = cv2.FaceRecognizerSF.create(str(SFACE_MODEL_PATH), "")

        # In-memory database of enrolled faces {name: feature_array}
        self.known_faces: Dict[str, np.ndarray] = {}

    def set_input_size(self, width: int, height: int) -> None:
        """Update detector input resolution to match the current camera frame."""
        if self.input_size != (width, height):
            self.input_size = (width, height)
            self.detector.setInputSize((width, height))

    def detect_faces(self, frame: np.ndarray) -> List[DetectedFace]:
        """Detect faces in the given frame and compute their embeddings."""
        h, w = frame.shape[:2]
        self.set_input_size(w, h)

        _, raw_faces = self.detector.detect(frame)
        if raw_faces is None or len(raw_faces) == 0:
            return []

        detected: List[DetectedFace] = []
        for raw in raw_faces:
            try:
                # Align and crop face for SFace
                aligned = self.recognizer.alignCrop(frame, raw)
                feature = self.recognizer.feature(aligned)
                detected.append(DetectedFace(raw, feature))
            except Exception as e:
                # Still include detected face even if feature extraction fails
                detected.append(DetectedFace(raw, None))

        return detected

    def match_features(self, feature1: np.ndarray, feature2: np.ndarray) -> float:
        """Compute cosine similarity score between two face embeddings.
        OpenCV SFace convention: score >= cosine_threshold means match.
        """
        if feature1 is None or feature2 is None:
            return 0.0
        return float(self.recognizer.match(feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE))

    def identify_face(self, feature: np.ndarray) -> Tuple[Optional[str], float]:
        """Match feature vector against known enrolled faces.
        Returns (name, score) if score >= threshold, else (None, best_score).
        """
        if feature is None or not self.known_faces:
            return None, 0.0

        best_name = None
        best_score = -1.0

        for name, known_feat in self.known_faces.items():
            score = self.match_features(feature, known_feat)
            if score > best_score:
                best_score = score
                best_name = name

        if best_score >= self.cosine_threshold:
            return best_name, best_score
        return None, best_score

    def enroll_face_from_image(self, name: str, image_path: Path) -> bool:
        """Enroll a face from an image file into the known faces database."""
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[FaceEngine] Error: Could not read image {image_path}")
            return False

        h, w = img.shape[:2]
        # Temporarily adapt input size
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        # Restore original input size
        self.detector.setInputSize(self.input_size)

        if faces is None or len(faces) == 0:
            print(f"[FaceEngine] Warning: No face detected in {image_path.name}")
            return False

        # Take largest detected face
        best_face = max(faces, key=lambda f: f[2] * f[3])
        aligned = self.recognizer.alignCrop(img, best_face)
        feature = self.recognizer.feature(aligned)

        self.known_faces[name] = feature
        print(f"[FaceEngine] Enrolled '{name}' from {image_path.name}")
        return True

    def load_known_faces(self, directory: Path) -> int:
        """Load all images from known_faces directory.
        Filename without extension is used as the person's name (e.g. scott.jpg -> 'scott').
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
        enrolled_count = 0

        for file_path in directory.iterdir():
            if file_path.suffix.lower() in valid_exts:
                name = file_path.stem.replace("_", " ").title()
                if self.enroll_face_from_image(name, file_path):
                    enrolled_count += 1

        print(f"[FaceEngine] Total enrolled faces loaded: {enrolled_count}")
        return enrolled_count
