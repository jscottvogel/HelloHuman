"""
HelloHuman - Main Application Entrypoint
Facial Recognition and Greeting System using OpenCV YuNet & SFace.
"""
import argparse
import sys
import time
from pathlib import Path
import cv2

from config import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_COOLDOWN_SECONDS,
    AUDIO_DIR,
    KNOWN_FACES_DIR,
    WINDOW_TITLE,
)
from src.audio_player import AudioPlayer
from src.face_engine import FaceEngine
from src.tracker import IdentityTracker
from src.display import DisplayRenderer


def parse_args():
    parser = argparse.ArgumentParser(
        description="HelloHuman - Facial Recognition Greeting System"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=DEFAULT_CAMERA_INDEX,
        help="Camera index (default: 0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_FRAME_WIDTH,
        help=f"Capture width (default: {DEFAULT_FRAME_WIDTH})",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_FRAME_HEIGHT,
        help=f"Capture height (default: {DEFAULT_FRAME_HEIGHT})",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=DEFAULT_COOLDOWN_SECONDS,
        help=f"Cooldown in seconds between greetings for the same person (default: {DEFAULT_COOLDOWN_SECONDS})",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Mute audio greetings",
    )
    parser.add_argument(
        "--audio-device",
        type=str,
        default=None,
        help="ALSA audio playback device on Linux/Pi (e.g. 'plughw:0,0' or 'plughw:1,0')",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Start in fullscreen mode",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI window",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("  HELLO HUMAN - Facial Recognition & Greeting System")
    print("=" * 60)

    # 1. Initialize Subsystems
    print("\n[1/4] Initializing Face Detection and Recognition Engine...")
    face_engine = FaceEngine(input_size=(args.width, args.height))

    print(f"\n[2/4] Loading enrolled faces from {KNOWN_FACES_DIR}...")
    face_engine.load_known_faces(KNOWN_FACES_DIR)

    print(f"\n[3/4] Initializing Audio Player from {AUDIO_DIR}...")
    audio_player = AudioPlayer(AUDIO_DIR, device=args.audio_device)
    playlist = audio_player.refresh_playlist()
    print(f"      Found {len(playlist)} WAV greeting files in rotation.")

    tracker = IdentityTracker(face_engine, cooldown_seconds=args.cooldown)
    renderer = DisplayRenderer(window_name=WINDOW_TITLE)

    # 2. Open Camera
    print(f"\n[4/4] Opening Camera (index {args.camera})...")
    # On Windows, try cv2.CAP_DSHOW for fast startup
    if sys.platform == "win32":
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(args.camera)
    else:
        cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print(f"Error: Could not open camera {args.camera}.")
        print("Please check your webcam connection and camera index.")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    # Read back actual resolution
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"      Camera started: {actual_w}x{actual_h}")
    face_engine.set_input_size(actual_w, actual_h)

    if not args.headless:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        if args.fullscreen:
            renderer.toggle_fullscreen()

    print("\nSystem running! Press 'q' or 'ESC' in the video window to quit.\n")

    # Metrics
    fps = 0.0
    frame_count = 0
    start_time = time.time()
    last_fps_time = time.time()
    last_audio_greeting = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Failed to grab frame from camera.")
                time.sleep(0.01)
                continue

            frame_count += 1
            now = time.time()

            # Compute smooth FPS
            dt = now - last_fps_time
            if dt >= 0.5:
                fps = frame_count / dt
                frame_count = 0
                last_fps_time = now

            # 1. Detect faces
            detected_faces = face_engine.detect_faces(frame)

            # 2. Track identities and cooldowns
            tracked_results = tracker.process_detected_faces(detected_faces)

            # 3. Check for greetings
            for res in tracked_results:
                if res.should_greet:
                    sound_name = "MUTED"
                    if not args.no_audio:
                        played = audio_player.play_random_greeting()
                        if played:
                            sound_name = played
                            last_audio_greeting = played

                    tracker.mark_greeted(res.identity_id)
                    res.should_greet = False
                    res.cooldown_remaining = tracker.cooldown_seconds
                    print(
                        f"👋 [GREETING] Greeted {res.display_name} "
                        f"(Similarity: {res.similarity_score:.2f}) -> Audio: {sound_name}"
                    )

            # 4. Display frame
            if not args.headless:
                display_frame = renderer.render(
                    frame,
                    tracked_results,
                    fps=fps,
                    last_audio_greeting=last_audio_greeting,
                    cooldown_setting=tracker.cooldown_seconds,
                )
                cv2.imshow(WINDOW_TITLE, display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                    break
                elif key in (ord("f"), ord("F")):
                    renderer.toggle_fullscreen()
                elif key in (ord("r"), ord("R")):
                    tracker.reset_cooldown()
                    print("🔄 Reset all cooldown timers.")
                elif key in (ord("g"), ord("G")):
                    # Force greeting for currently visible faces
                    for res in tracked_results:
                        tracker.reset_cooldown(res.identity_id)
                    print("⚡ Force greeting triggered for visible humans.")

    except KeyboardInterrupt:
        print("\nShutdown requested by user (Ctrl+C).")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"Session ended. Total runtime: {elapsed:.1f}s")
        print(f"Tracked unique individuals: {len(tracker.identities)}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
