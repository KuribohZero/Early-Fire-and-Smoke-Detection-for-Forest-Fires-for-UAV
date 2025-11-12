# ---------------- config.py ----------------
from datetime import datetime
import os
import cv2

# Paths
BASE_DIR = "/home/jugmentz/drone/boot_videos"

# Cameras
FRAME_SIZE = (640, 480)
COMBINED_SIZE = (1280, 480)
THERMAL_DEVICE = "/dev/video0"     # change if needed

# Timing
CAMERA_WARMUP = 10                 # seconds
FPS = 20.0
SAVE_INTERVAL = 60                 # new file every N seconds
STATUS_INTERVAL = 30               # console + MAVLink update

# Video
FOURCC = cv2.VideoWriter_fourcc(*"XVID")  # AVI is crash-resilient

# Models
VISUAL_MODEL_NAME = "yolov11n_rgb--640x640"
THERMAL_MODEL_NAME = "yolov11n_ir--640x640"
ZOO_URL = "model_zoo"

# MAVLink
MAVLINK_DEVICE = "/dev/ttyAMA0"
MAVLINK_BAUD = 57600
MAVLINK_SEVERITY_INFO = 6

# Session folder helper
def make_session_dir():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(BASE_DIR, ts)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir
