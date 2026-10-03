"""
OpenCV display renderer and HUD overlay for HelloHuman.
"""
from typing import List, Optional
import cv2
import numpy as np

from config import SHOW_LANDMARKS, SHOW_STATUS_BAR
from src.tracker import TrackedFaceResult


class DisplayRenderer:
    def __init__(
        self,
        window_name: str = "HelloHuman",
        show_landmarks: bool = SHOW_LANDMARKS,
        show_status_bar: bool = SHOW_STATUS_BAR,
    ):
        self.window_name = window_name
        self.show_landmarks = show_landmarks
        self.show_status_bar = show_status_bar
        self.is_fullscreen = False

    def toggle_fullscreen(self) -> bool:
        """Toggle fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        prop = cv2.WINDOW_FULLSCREEN if self.is_fullscreen else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, prop)
        return self.is_fullscreen

    def draw_text_box(
        self,
        frame: np.ndarray,
        text: str,
        pos: tuple,
        font_scale: float = 0.5,
        text_color: tuple = (255, 255, 255),
        bg_color: tuple = (0, 0, 0),
        thickness: int = 1,
        padding: int = 4,
    ) -> None:
        """Draw text with an opaque background rectangle for crisp visibility."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (w, h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x, y = pos
        # Background rectangle
        cv2.rectangle(
            frame,
            (x - padding, y - h - padding),
            (x + w + padding, y + baseline + padding),
            bg_color,
            -1,
        )
        # Text string
        cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)

    def render(
        self,
        frame: np.ndarray,
        tracked_results: List[TrackedFaceResult],
        fps: float = 0.0,
        last_audio_greeting: Optional[str] = None,
        cooldown_setting: float = 60.0,
    ) -> np.ndarray:
        """Render HUD bounding boxes, face tags, and status bar on frame."""
        output = frame.copy()
        h, w = output.shape[:2]

        # 1. Draw detected and tracked faces
        for res in tracked_results:
            bx, by, bw, bh = res.detected_face.bbox

            if res.should_greet:
                color = (0, 230, 0)      # Bright Green for greeting trigger
                status_str = "GREETED"
            else:
                color = (255, 170, 0)    # Amber/Cyan for cooldown active
                status_str = f"Cooldown: {int(res.cooldown_remaining)}s"

            # Draw rounded/corner-accented bounding box
            cv2.rectangle(output, (bx, by), (bx + bw, by + bh), color, 2)

            # Draw facial landmarks if enabled
            if self.show_landmarks:
                for lx, ly in res.detected_face.landmarks:
                    cv2.circle(output, (lx, ly), 3, (0, 255, 255), -1)

            # Face label
            label = f"{res.display_name} [{status_str}]"
            tag_y = max(24, by - 8)
            self.draw_text_box(
                output,
                label,
                (bx, tag_y),
                font_scale=0.55,
                text_color=(255, 255, 255),
                bg_color=(30, 30, 30),
                thickness=1,
            )

        # 2. Top Status Bar
        if self.show_status_bar:
            # Semi-transparent header banner
            header_height = 42
            overlay = output.copy()
            cv2.rectangle(overlay, (0, 0), (w, header_height), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.75, output, 0.25, 0, output)

            # Left stats
            face_count = len(tracked_results)
            status_text = f"HELLO HUMAN | Faces: {face_count} | FPS: {fps:.1f}"
            cv2.putText(
                output,
                status_text,
                (14, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 200),
                1,
                cv2.LINE_AA,
            )

            # Right audio stats
            audio_text = (
                f"Audio: {last_audio_greeting}"
                if last_audio_greeting
                else f"Cooldown: {int(cooldown_setting)}s"
            )
            (aw, _), _ = cv2.getTextSize(audio_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.putText(
                output,
                audio_text,
                (max(w - aw - 14, 250), 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

        # 3. Bottom controls banner (compact)
        bot_bar_height = 24
        overlay_bot = output.copy()
        cv2.rectangle(overlay_bot, (0, h - bot_bar_height), (w, h), (15, 15, 15), -1)
        cv2.addWeighted(overlay_bot, 0.8, output, 0.2, 0, output)

        controls_text = "[Q] Quit  |  [G] Force Greet  |  [R] Reset Cooldowns  |  [F] Fullscreen"
        cv2.putText(
            output,
            controls_text,
            (14, h - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (170, 170, 170),
            1,
            cv2.LINE_AA,
        )

        return output
