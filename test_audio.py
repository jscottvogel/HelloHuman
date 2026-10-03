"""
HelloHuman - Audio Troubleshooting and Diagnostic Utility
Run this script directly on your Raspberry Pi or PC to test and diagnose audio playback.
Usage:
    python test_audio.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from config import AUDIO_DIR


def run_cmd(cmd_list):
    """Run a command and return stdout, stderr, and exit code."""
    try:
        res = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except FileNotFoundError:
        return "", f"Command '{cmd_list[0]}' not found.", -1
    except Exception as e:
        return "", str(e), -1


def check_audio_subsystem():
    print("=" * 60)
    print("  AUDIO SUBSYSTEM DIAGNOSTICS")
    print("=" * 60)
    print(f"Platform: {sys.platform}")

    test_wav = AUDIO_DIR / "hello_human.wav"
    if not test_wav.exists():
        print(f"Error: Test audio file not found at {test_wav}")
        return
    print(f"Found test sound file: {test_wav.name} ({test_wav.stat().st_size:,} bytes)")

    if sys.platform == "win32":
        print("\n[Windows Audio Check]")
        try:
            import winsound
            print("  winsound module available: YES")
            print("  Playing test sound asynchronously...")
            winsound.PlaySound(str(test_wav), winsound.SND_FILENAME)
            print("  Playback completed successfully.")
        except Exception as e:
            print(f"  Playback error: {e}")
        return

    # Linux / Raspberry Pi Audio Check
    print("\n[Linux / Raspberry Pi Audio Check]")

    # 1. Check tools
    for tool in ["aplay", "amixer", "alsamixer", "pulseaudio", "pipewire"]:
        loc = shutil.which(tool)
        status = f"INSTALLED ({loc})" if loc else "NOT INSTALLED"
        print(f"  {tool.ljust(12)}: {status}")

    # 2. List ALSA playback cards
    print("\n[Detected Audio Cards (aplay -l)]")
    stdout, stderr, code = run_cmd(["aplay", "-l"])
    if code != 0 or not stdout:
        print("  WARNING: No audio cards detected or aplay returned an error:")
        print(f"  {stderr}")
    else:
        for line in stdout.splitlines():
            print(f"  {line}")

    # 3. Check mixer volumes
    print("\n[Volume Levels (amixer)]")
    stdout_mix, _, _ = run_cmd(["amixer", "scontrols"])
    controls = re.findall(r"'([^']+)'", stdout_mix)
    if controls:
        for ctrl in controls:
            sget_out, _, _ = run_cmd(["amixer", "sget", ctrl])
            # Check percentage and mute state
            vol_match = re.search(r"\[(\d+%)\]", sget_out)
            mute_match = re.search(r"\[(on|off)\]", sget_out)
            vol_str = vol_match.group(1) if vol_match else "unknown"
            state_str = "MUTED" if mute_match and mute_match.group(1) == "off" else "ACTIVE"
            print(f"  Control '{ctrl}': {vol_str} ({state_str})")
            if mute_match and mute_match.group(1) == "off":
                print(f"    -> FIX: Run 'amixer sset \"{ctrl}\" unmute' and 'amixer sset \"{ctrl}\" 100%'")
    else:
        print("  No simple mixer controls reported by default.")

    # 4. Interactive or step-by-step playback tests
    print("\n" + "=" * 60)
    print("  AUDIO PLAYBACK TESTS")
    print("=" * 60)

    # Test 0: PipeWire / PulseAudio playback
    if shutil.which("pw-play"):
        print("\n0a. Testing PipeWire output ('pw-play audio/hello_human.wav')...")
        out, err, code = run_cmd(["pw-play", str(test_wav)])
        if code == 0:
            print("   Command succeeded! (PipeWire audio played)")
        else:
            print(f"   pw-play failed: {err}")

    if shutil.which("paplay"):
        print("\n0b. Testing PulseAudio/PipeWire output ('paplay audio/hello_human.wav')...")
        out, err, code = run_cmd(["paplay", str(test_wav)])
        if code == 0:
            print("   Command succeeded! (PulseAudio audio played)")
        else:
            print(f"   paplay failed: {err}")

    # Test 1: Default ALSA playback
    print("\n1. Testing Default ALSA output ('aplay audio/hello_human.wav')...")
    out, err, code = run_cmd(["aplay", str(test_wav)])
    if code == 0:
        print("   Command succeeded! Did you hear 'Hello Human!'?")
    else:
        print(f"   Command failed with code {code}:")
        print(f"   Stderr: {err}")

    # Test 2: Specific cards if available
    card_devices = re.findall(r"card (\d+): [^,]+, device (\d+):", stdout)
    if card_devices:
        print("\n2. Testing individual detected audio hardware devices:")
        for card_id, dev_id in card_devices:
            dev_name = f"plughw:{card_id},{dev_id}"
            print(f"\n   Testing device: {dev_name} ...")
            out, err, code = run_cmd(["aplay", "-D", dev_name, str(test_wav)])
            if code == 0:
                print(f"   Command succeeded on {dev_name}!")
                print(f"   -> If you heard sound from this device, you can run HelloHuman with:")
                print(f"      python3 main.py --audio-device {dev_name}")
            else:
                print(f"   Device {dev_name} failed: {err}")

    print("\n" + "=" * 60)
    print("  SUMMARY & COMMON RASPBERRY PI AUDIO FIXES")
    print("=" * 60)
    print("1. If using the 3.5mm Headphone Jack:")
    print("   Run: sudo raspi-config -> System Options -> Audio -> Headphones")
    print("   And set volume: amixer sset Headphone 100% unmute")
    print("2. If using HDMI Monitor Speakers:")
    print("   Run: sudo raspi-config -> System Options -> Audio -> HDMI")
    print("3. If using USB Speaker / Audio Adapter:")
    print("   Check which card number it is in 'aplay -l' above, then pass:")
    print("   python3 main.py --audio-device plughw:<card_number>,0")
    print("=" * 60)


if __name__ == "__main__":
    check_audio_subsystem()
