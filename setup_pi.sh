#!/usr/bin/env bash
# HelloHuman - Raspberry Pi 3 Setup Script
set -e

echo "=================================================="
echo "  Setting up HelloHuman on Raspberry Pi 3"
echo "=================================================="

# 1. Update package lists
echo "[1/4] Installing system dependencies (OpenCV, ALSA audio, tools)..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    python3-numpy \
    alsa-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    espeak-ng

# 2. Setup Python Virtual Environment
echo "[2/4] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv --system-site-packages
fi
source venv/bin/activate

# 3. Verify OpenCV & Python environment
echo "[3/4] Verifying Python environment and OpenCV..."
if ! python3 -c "import cv2" &> /dev/null; then
    echo "  cv2 not detected in virtualenv, installing opencv-python-headless..."
    pip install --upgrade pip
    pip install opencv-python-headless || pip install opencv-python
fi
python3 -c "import cv2; print('  OpenCV loaded successfully:', cv2.__version__)"

# 4. Download models & generate audio
echo "[4/4] Ensuring models and audio files..."
python3 download_models.py
python3 generate_audio.py

echo ""
echo "=================================================="
echo "  Setup Complete!"
echo "  To launch HelloHuman:"
echo "    source venv/bin/activate"
echo "    python3 main.py"
echo "=================================================="
