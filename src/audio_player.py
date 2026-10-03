"""
Cross-platform non-blocking WAV audio player with greeting rotation.
"""
import os
import random
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional


class AudioPlayer:
    def __init__(self, audio_dir: Path, min_playback_gap: float = 2.0):
        self.audio_dir = Path(audio_dir)
        self.min_playback_gap = min_playback_gap
        self.last_played_time = 0.0
        self.last_played_file: Optional[Path] = None
        self._playlist: List[Path] = []
        self._playlist_index = 0
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None

        # Check platform audio player
        self.is_windows = sys.platform == "win32"
        self.linux_player = None
        if not self.is_windows:
            self.linux_player = (
                shutil.which("aplay")
                or shutil.which("paplay")
                or shutil.which("play")
            )

        self.refresh_playlist()

    def refresh_playlist(self) -> List[Path]:
        """Scan audio directory for all .wav files."""
        with self._lock:
            if not self.audio_dir.exists():
                self._playlist = []
                return []

            wav_files = sorted(list(self.audio_dir.glob("*.wav")))
            # Randomize playlist order
            random.shuffle(wav_files)
            self._playlist = wav_files
            self._playlist_index = 0
            return list(self._playlist)

    def get_next_sound(self) -> Optional[Path]:
        """Get next WAV sound in the rotation cycle."""
        with self._lock:
            if not self._playlist:
                self.refresh_playlist()
                if not self._playlist:
                    return None

            if self._playlist_index >= len(self._playlist):
                # Reshuffle when cycle completes, ensuring first isn't same as previous
                prev = self._playlist[-1] if self._playlist else None
                random.shuffle(self._playlist)
                if len(self._playlist) > 1 and self._playlist[0] == prev:
                    # Swap first with last to prevent immediate repeat
                    self._playlist[0], self._playlist[-1] = self._playlist[-1], self._playlist[0]
                self._playlist_index = 0

            sound_file = self._playlist[self._playlist_index]
            self._playlist_index += 1
            return sound_file

    def play_wav(self, file_path: Path) -> bool:
        """Play a WAV file asynchronously without blocking the UI thread."""
        now = time.time()
        with self._lock:
            if now - self.last_played_time < self.min_playback_gap:
                # Still within minimum gap between consecutive playbacks
                return False
            self.last_played_time = now
            self.last_played_file = file_path

        try:
            if self.is_windows:
                import winsound
                # Play asynchronously
                winsound.PlaySound(
                    str(file_path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return True
            else:
                if self.linux_player:
                    # Clean up old process if needed
                    if self._process and self._process.poll() is None:
                        try:
                            self._process.terminate()
                        except Exception:
                            pass
                    self._process = subprocess.Popen(
                        [self.linux_player, "-q", str(file_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                else:
                    print(f"[AudioPlayer] Warning: No audio player (aplay/paplay) found on Linux.")
                    return False
        except Exception as e:
            print(f"[AudioPlayer] Error playing audio: {e}")
            return False

    def play_random_greeting(self) -> Optional[str]:
        """Pick the next rotating greeting WAV and play it asynchronously."""
        sound = self.get_next_sound()
        if sound and sound.exists():
            if self.play_wav(sound):
                return sound.name
        return None
