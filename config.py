"""
HelloHuman - Centralized Configuration
"""
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
AUDIO_DIR = BASE_DIR / "audio"
KNOWN_FACES_DIR = BASE_DIR / "known_faces"

# Model filenames
YUNET_MODEL_FILE = "face_detection_yunet_2023mar.onnx"
SFACE_MODEL_FILE = "face_recognition_sface_2021dec.onnx"

YUNET_MODEL_PATH = MODELS_DIR / YUNET_MODEL_FILE
SFACE_MODEL_PATH = MODELS_DIR / SFACE_MODEL_FILE

# Model Download URLs (OpenCV Zoo)
YUNET_DOWNLOAD_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
SFACE_DOWNLOAD_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)

# Video settings
DEFAULT_CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", 0))
DEFAULT_FRAME_WIDTH = int(os.environ.get("FRAME_WIDTH", 640))
DEFAULT_FRAME_HEIGHT = int(os.environ.get("FRAME_HEIGHT", 480))

# Face Detection Settings (YuNet)
DETECTION_SCORE_THRESHOLD = 0.75   # Minimum confidence score for face detection
DETECTION_NMS_THRESHOLD = 0.3      # Non-maximum suppression threshold
DETECTION_TOP_K = 10               # Maximum number of faces to detect per frame

# Face Recognition Settings (SFace)
# Cosine similarity threshold recommended by OpenCV SFace:
# Score >= 0.363 means same identity
RECOGNITION_COSINE_THRESHOLD = 0.363

# Greeting & Cooldown Settings
# Number of seconds before greeting the same person again
DEFAULT_COOLDOWN_SECONDS = float(os.environ.get("COOLDOWN_SECONDS", 60.0))

# Display settings
SHOW_LANDMARKS = False
SHOW_STATUS_BAR = True
WINDOW_TITLE = "HelloHuman - Facial Recognition Greeting System"
