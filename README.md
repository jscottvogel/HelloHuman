# HelloHuman 🤖👋

A real-time facial recognition and greeting system built with OpenCV deep learning, designed for Raspberry Pi 3 and cross-platform desktop testing.

HelloHuman watches a video camera feed, detects human faces, recognizes distinct individuals, and greets each person with rotating audio greetings (e.g. *"Hello Human!"*, *"Greetings, Earthling!"*). It enforces a per-person cooldown (e.g. 60–120 seconds) so that the same person is not greeted repeatedly while remaining in front of the camera.

---

## Features

- **Lightweight Deep Learning**: Uses OpenCV's official **YuNet** face detector (~230 KB) and **SFace** face recognizer (~38 MB). Highly optimized for low-power edge devices like Raspberry Pi 3 (1 GB RAM) without requiring heavy dependencies like `dlib` or `PyTorch`.
- **Identity Recognition & Per-Person Cooldown**: Tracks distinct visitors dynamically, greeting each person once and enforcing a configurable cooldown timer before greeting them again.
- **Enrolled Faces Support**: Drop photos of people into `known_faces/` (e.g., `scott.jpg`) to recognize and greet specific people by name!
- **Rotating Audio Greetings**: Cycles through pre-rendered humorous WAV audio files in `audio/` with non-blocking, zero-latency playback. Drop your own custom `.wav` files into `audio/` anytime.
- **Live HUD Display**: Real-time OpenCV display with color-coded bounding boxes (Green = Greeted, Blue/Orange = Cooldown active), face tags, FPS counter, and status bar.
- **Cross-Platform**: Runs natively on **Windows** (using `winsound` audio) and **Raspberry Pi Linux** (using `aplay`).

---

## Directory Structure

```
HelloHuman/
├── config.py                 # Centralized configuration (cooldown, camera index, paths)
├── download_models.py        # Automated downloader for YuNet and SFace ONNX models
├── generate_audio.py         # Greeting audio synthesizer & fallback generator
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── setup_pi.sh               # Raspberry Pi 3 quick setup script
├── audio/                    # WAV greeting files directory
│   ├── hello_human.wav
│   ├── greetings_earthling.wav
│   ├── carbon_lifeform.wav
│   ├── beep_boop.wav
│   ├── welcome_human.wav
│   └── nice_face.wav
├── models/                   # Deep learning ONNX models (auto-downloaded)
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
├── known_faces/              # Put enrolled face photos here (e.g., scott.jpg)
└── src/
    ├── audio_player.py       # Cross-platform non-blocking WAV audio player
    ├── display.py            # OpenCV HUD and overlay renderer
    ├── face_engine.py        # YuNet & SFace face detection and feature extraction
    └── tracker.py            # Identity matching and cooldown tracking
```

---

## Quick Start (Windows Local Testing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Models & Generate Audio
```bash
python download_models.py
python generate_audio.py
```

### 3. Run HelloHuman
```bash
python main.py
```

### Keyboard Shortcuts in Video Window:
- `Q` or `ESC`: Quit application
- `F`: Toggle Fullscreen mode
- `R`: Reset all cooldown timers
- `G`: Force greeting for all currently visible faces

---

## Raspberry Pi 3 Deployment

### Hardware Required:
- Raspberry Pi 3 (Raspberry Pi OS 32-bit or 64-bit)
- USB Webcam (or Pi Camera with V4L2 enabled)
- USB Speaker / 3.5mm Headphone Speaker
- HDMI Monitor

### Automated Setup:
1. Clone the repository onto the Raspberry Pi:
   ```bash
   git clone https://github.com/jscottvogel/HelloHuman.git
   cd HelloHuman
   ```
2. Run the setup script:
   ```bash
   chmod +x setup_pi.sh
   ./setup_pi.sh
   ```
3. Run HelloHuman:
   ```bash
   source venv/bin/activate
   python3 main.py
   ```

---

## Configuration & Customization

You can pass command-line arguments to `main.py` or modify `config.py`:

```bash
# Change cooldown to 120 seconds (2 minutes)
python main.py --cooldown 120

# Run in fullscreen mode (ideal for monitor display)
python main.py --fullscreen

# Specify a different camera index
python main.py --camera 1

# Mute audio for silent testing
python main.py --no-audio
```

### Adding Known Faces
To recognize a specific person:
1. Place a clear photo of the person in the `known_faces/` folder.
2. Name the file with their name (e.g. `scott.jpg`, `sarah.png`).
3. Restart or run `main.py`. The system will automatically detect the face, extract its embedding, and identify the person by name!

### Adding Custom Greetings
Drop any `.wav` audio file into the `audio/` directory. The audio player automatically discovers and rotates through all `.wav` files.
