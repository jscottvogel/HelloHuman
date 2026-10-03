"""
Generate funny 'Hello Human' WAV greeting files.
Supports Windows SAPI, Linux espeak/espeak-ng, and synthetic fallback.
Generated WAV files are saved directly into the audio/ directory.
"""
import math
import os
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

from config import AUDIO_DIR

GREETINGS = [
    ("hello_human.wav", "Hello Human!"),
    ("greetings_earthling.wav", "Greetings, earthling! It is a pleasure to detect you."),
    ("carbon_lifeform.wav", "Hello carbon-based lifeform. How is your day going?"),
    ("beep_boop.wav", "Beep boop! Human detected. Hello there!"),
    ("welcome_human.wav", "Ah, a human in my visual sensor! Welcome!"),
    ("nice_face.wav", "I see you, human. That is a very nice face you have there."),
    ("live_long_and_prosper.wav", "Live long and prosper."),
]


def generate_with_sapi(text: str, output_path: Path) -> bool:
    """Generate audio using Windows SAPI (pywin32)."""
    try:
        import win32com.client
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        # 3 = SSFMCreateForWrite
        stream.Open(str(output_path), 3)
        voice.AudioOutputStream = stream
        voice.Speak(text)
        stream.Close()
        return True
    except Exception as e:
        print(f"  SAPI generation failed: {e}")
        return False


def generate_with_espeak(text: str, output_path: Path) -> bool:
    """Generate audio using espeak or espeak-ng on Linux/Raspberry Pi."""
    tts_cmd = shutil.which("espeak-ng") or shutil.which("espeak")
    if not tts_cmd:
        return False
    try:
        subprocess.run(
            [tts_cmd, "-w", str(output_path), "-s", "150", "-p", "50", text],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"  espeak generation failed: {e}")
        return False


def generate_synth_chime(output_path: Path, freqs=(440, 554, 659, 880), duration=0.15) -> bool:
    """Fallback: synthesize friendly multi-tone greeting chimes in pure Python."""
    try:
        sample_rate = 22050
        num_samples_per_tone = int(sample_rate * duration)
        with wave.open(str(output_path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            samples = []
            for freq in freqs:
                for i in range(num_samples_per_tone):
                    t = float(i) / sample_rate
                    # Envelope decay
                    env = max(0.0, 1.0 - (i / num_samples_per_tone))
                    value = int(32767.0 * 0.5 * env * math.sin(2.0 * math.pi * freq * t))
                    samples.append(struct.pack("<h", value))

            wav_file.writeframes(b"".join(samples))
        return True
    except Exception as e:
        print(f"  Synthetic chime generation failed: {e}")
        return False


def generate_all_greetings(force: bool = False) -> None:
    """Generate all default WAV greetings into the audio directory."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating audio files into {AUDIO_DIR}...")

    for filename, text in GREETINGS:
        target = AUDIO_DIR / filename
        if target.exists() and not force:
            print(f"  Audio file already exists: {filename}")
            continue

        print(f"  Creating '{filename}' -> \"{text}\"")
        success = False

        if sys.platform == "win32":
            success = generate_with_sapi(text, target)

        if not success:
            success = generate_with_espeak(text, target)

        if not success:
            print(f"  Using pleasant synthesizer fallback for {filename}...")
            # Vary tones slightly
            base_f = 440 + (hash(filename) % 200)
            success = generate_synth_chime(target, freqs=(base_f, int(base_f * 1.25), int(base_f * 1.5)))

        if success and target.exists():
            print(f"    OK ({target.stat().st_size:,} bytes)")
        else:
            print(f"    FAILED to generate {filename}")


if __name__ == "__main__":
    force_gen = "--force" in sys.argv
    generate_all_greetings(force=force_gen)
