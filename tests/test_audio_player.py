"""
Tests for AudioPlayer.
"""
import sys
import time
from pathlib import Path
import pytest

from config import AUDIO_DIR
from src.audio_player import AudioPlayer


def test_audio_playlist_discovery():
    player = AudioPlayer(AUDIO_DIR)
    playlist = player.refresh_playlist()
    assert len(playlist) >= 6
    filenames = [p.name for p in playlist]
    assert "hello_human.wav" in filenames


def test_audio_rotation_cycling():
    player = AudioPlayer(AUDIO_DIR)
    playlist = player.refresh_playlist()
    count = len(playlist)
    assert count > 0

    collected = []
    for _ in range(count):
        sound = player.get_next_sound()
        assert sound is not None
        collected.append(sound.name)

    # All unique files in one cycle
    assert len(set(collected)) == count


def test_audio_min_playback_gap(tmp_path):
    # Create dummy wav file
    dummy_wav = tmp_path / "test.wav"
    dummy_wav.write_bytes(b"RIFF....WAVEfmt ....data....")

    player = AudioPlayer(tmp_path, min_playback_gap=1.0)
    # First play should succeed
    res1 = player.play_wav(dummy_wav)
    assert res1 is True

    # Immediate second play within gap should be rejected
    res2 = player.play_wav(dummy_wav)
    assert res2 is False
