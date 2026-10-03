"""
Tests for IdentityTracker (per-person cooldown and multi-human tracking).
"""
import time
import numpy as np
import pytest

from src.face_engine import DetectedFace, FaceEngine
from src.tracker import IdentityTracker


def create_dummy_face(feature_vec, bbox=(10, 10, 100, 100), score=0.95):
    """Helper to create a synthetic DetectedFace with 15-element raw array."""
    raw = np.zeros(15, dtype=np.float32)
    raw[0:4] = bbox
    raw[14] = score
    return DetectedFace(raw, feature=feature_vec)


def test_tracker_first_greeting_and_cooldown():
    engine = FaceEngine(input_size=(320, 240))
    tracker = IdentityTracker(engine, cooldown_seconds=60.0)

    # Face A
    feat_a = np.random.randn(1, 128).astype(np.float32)
    feat_a /= np.linalg.norm(feat_a)
    face_a = create_dummy_face(feat_a)

    # First detection -> Should greet!
    res1 = tracker.process_detected_faces([face_a])
    assert len(res1) == 1
    assert res1[0].should_greet is True
    assert res1[0].identity_id == "visitor_1"
    assert res1[0].cooldown_remaining == 0.0

    # Mark greeted
    tracker.mark_greeted(res1[0].identity_id)

    # Immediate second detection of Person A -> Should NOT greet (cooldown active)
    res2 = tracker.process_detected_faces([face_a])
    assert len(res2) == 1
    assert res2[0].should_greet is False
    assert res2[0].identity_id == "visitor_1"
    assert res2[0].cooldown_remaining > 50.0


def test_tracker_independent_person_greeting():
    """Option B requirement: Person A is in cooldown, but Person B enters and is greeted independently."""
    engine = FaceEngine(input_size=(320, 240))
    tracker = IdentityTracker(engine, cooldown_seconds=60.0)

    # Person A
    feat_a = np.zeros((1, 128), dtype=np.float32)
    feat_a[0, 0] = 1.0  # Unit vector on dim 0
    face_a = create_dummy_face(feat_a)

    # Person B (orthogonal identity)
    feat_b = np.zeros((1, 128), dtype=np.float32)
    feat_b[0, 50] = 1.0  # Unit vector on dim 50
    face_b = create_dummy_face(feat_b)

    # 1. Greet Person A
    res_a = tracker.process_detected_faces([face_a])
    assert res_a[0].should_greet is True
    tracker.mark_greeted(res_a[0].identity_id)

    # 2. Both Person A and Person B in frame
    res_both = tracker.process_detected_faces([face_a, face_b])
    assert len(res_both) == 2

    # Person A is in cooldown
    res_a_check = [r for r in res_both if r.identity_id == res_a[0].identity_id][0]
    assert res_a_check.should_greet is False

    # Person B is NEW and should be greeted!
    res_b_check = [r for r in res_both if r.identity_id != res_a[0].identity_id][0]
    assert res_b_check.should_greet is True
    assert res_b_check.identity_id == "visitor_2"


def test_tracker_reset_cooldown():
    engine = FaceEngine(input_size=(320, 240))
    tracker = IdentityTracker(engine, cooldown_seconds=60.0)

    feat = np.random.randn(1, 128).astype(np.float32)
    feat /= np.linalg.norm(feat)
    face = create_dummy_face(feat)

    res1 = tracker.process_detected_faces([face])
    tracker.mark_greeted(res1[0].identity_id)

    # Reset cooldowns
    tracker.reset_cooldown()

    # Next detection should greet again
    res2 = tracker.process_detected_faces([face])
    assert res2[0].should_greet is True
