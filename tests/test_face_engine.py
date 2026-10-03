"""
Tests for FaceEngine (YuNet face detection & SFace recognition).
"""
import numpy as np
import pytest

from config import YUNET_MODEL_PATH, SFACE_MODEL_PATH
from src.face_engine import FaceEngine


def test_face_engine_initialization():
    engine = FaceEngine(input_size=(320, 240))
    assert engine.detector is not None
    assert engine.recognizer is not None
    assert engine.input_size == (320, 240)


def test_face_engine_input_size_update():
    engine = FaceEngine(input_size=(320, 240))
    engine.set_input_size(640, 480)
    assert engine.input_size == (640, 480)


def test_face_engine_similarity_matching():
    engine = FaceEngine(input_size=(320, 240))

    # Generate a synthetic normalized embedding vector
    vec1 = np.random.randn(1, 128).astype(np.float32)
    vec1 /= np.linalg.norm(vec1)

    # Self-match cosine should be 1.0 (or extremely close)
    self_score = engine.match_features(vec1, vec1)
    assert pytest.approx(self_score, rel=1e-3) == 1.0

    # Orthogonal / different vector should have much lower score
    vec2 = np.random.randn(1, 128).astype(np.float32)
    vec2 /= np.linalg.norm(vec2)
    diff_score = engine.match_features(vec1, vec2)
    assert diff_score < 0.8
