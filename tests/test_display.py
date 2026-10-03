"""
Tests for DisplayRenderer.
"""
import numpy as np
import pytest

from src.display import DisplayRenderer
from src.face_engine import DetectedFace
from src.tracker import TrackedFaceResult


def test_display_render_output_shape():
    renderer = DisplayRenderer()
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    raw_face = np.zeros(15, dtype=np.float32)
    raw_face[0:4] = [50, 50, 100, 100]
    raw_face[14] = 0.95
    det_face = DetectedFace(raw_face)

    tracked = TrackedFaceResult(
        detected_face=det_face,
        identity_id="visitor_1",
        display_name="Human #1",
        is_enrolled=False,
        similarity_score=1.0,
        should_greet=True,
        cooldown_remaining=0.0,
    )

    rendered = renderer.render(
        dummy_frame,
        [tracked],
        fps=30.0,
        last_audio_greeting="hello_human.wav",
        cooldown_setting=60.0,
    )

    assert rendered.shape == dummy_frame.shape
    assert rendered.dtype == np.uint8
    # Frame was modified with overlays
    assert not np.array_equal(rendered, dummy_frame)
