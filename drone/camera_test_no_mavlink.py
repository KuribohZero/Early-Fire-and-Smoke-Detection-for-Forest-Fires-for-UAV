#!/usr/bin/env python3
# ------------------------------------------------------------

import cv2
import os
import time
import threading
import numpy as np
from datetime import datetime
from picamera2 import Picamera2
import degirum as dg

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------
BASE_DIR = "/media/jugmentz/james/boot_videos"
SAVE_INTERVAL = 120       # seconds between new files
CAMERA_WARMUP = 10       # seconds before recording starts
FPS = 20.0
FRAME_SIZE = (640, 480)
COMBINED_SIZE = (1280, 480)
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
thermal_device = "/dev/video0"   # adjust if needed

# ------------------------------------------------------------
# CREATE NEW SESSION FOLDER (DATE + TIME)
# ------------------------------------------------------------
start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
SESSION_DIR = os.path.join(BASE_DIR, start_timestamp)
os.makedirs(SESSION_DIR, exist_ok=True)
print(f"💾 Session folder created: {SESSION_DIR}")

# ------------------------------------------------------------
# HELPER FUNCTION – create new writers
# ------------------------------------------------------------
def create_video_writers():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    visual_path = os.path.join(SESSION_DIR, f"visual_{ts}.mp4")
    thermal_path = os.path.join(SESSION_DIR, f"thermal_{ts}.mp4")
    combined_path = os.path.join(SESSION_DIR, f"combined_{ts}.mp4")

    out_visual = cv2.VideoWriter(visual_path, FOURCC, FPS, FRAME_SIZE)
    out_thermal = cv2.VideoWriter(thermal_path, FOURCC, FPS, FRAME_SIZE)
    out_combined = cv2.VideoWriter(combined_path, FOURCC, FPS, COMBINED_SIZE)

    print(f"🎞️ New recording segment started at {ts}")
    return out_visual, out_thermal, out_combined

# ------------------------------------------------------------
# LOAD YOLO MODEL (HAILO)
# ------------------------------------------------------------
print("🧠 Loading Hailo inference engine...")
try:
    inference_host = dg.connect(inference_host_address="@local", zoo_url="model_zoo")
    model_list = inference_host.list_models(device_type="HAILORT/HAILO8L")

    if not model_list:
        print("❌ No models found on Hailo device.")
        exit(1)

    visual_model = dg.load_model(
        model_name="yolov11n_rgb--640x640",
        inference_host_address="@local",
        zoo_url="model_zoo",
        overlay_show_probabilities=True
    )
    print("✅ YOLO model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit(1)

# ------------------------------------------------------------
# INITIALIZE VISUAL CAMERA
# ------------------------------------------------------------
visual_available = False
try:
    info = Picamera2.global_camera_info()
    if info:
        visual_available = True
        visualCapture = Picamera2()
        config = visualCapture.create_video_configuration(main={"size": FRAME_SIZE})
        visualCapture.configure(config)
        visualCapture.start()
        print("📷 Visual camera initialized.")
    else:
        print("❌ No visual camera found.")
except Exception as e:
    print(f"❌ Error initializing visual camera: {e}")

# ------------------------------------------------------------
# INITIALIZE THERMAL CAMERA
# ------------------------------------------------------------
thermal_available = False
if os.path.exists(thermal_device):
    thermalCapture = cv2.VideoCapture(thermal_device, cv2.CAP_V4L2)
    thermalCapture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
    thermalCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
    if thermalCapture.isOpened():
        thermal_available = True
        print("🌡️ Thermal camera initialized.")
    else:
        print(f"❌ Failed to open thermal camera at {thermal_device}.")
else:
    print(f"❌ Thermal device {thermal_device} not found.")

if not (visual_available or thermal_available):
    print("❌ No cameras available. Exiting.")
    exit(1)

# ------------------------------------------------------------
# CAMERA WARM-UP PERIOD
# ------------------------------------------------------------
print(f"⏳ Warming up cameras for {CAMERA_WARMUP} seconds...")
time.sleep(CAMERA_WARMUP)
print("✅ Camera warm-up complete. Starting recording...")

# ------------------------------------------------------------
# START THREADS AND WRITERS
# ------------------------------------------------------------
out_visual, out_thermal, out_combined = create_video_writers()
last_save_time = time.time()

thermal_frame = np.zeros((FRAME_SIZE[1], FRAME_SIZE[0], 3), dtype=np.uint8)
thermal_lock = threading.Lock()
thermal_running = True

def thermal_loop():
    global thermal_frame, out_thermal
    print("🧵 Thermal capture thread started.")
    while thermal_running and thermal_available:
        ret, frame = thermalCapture.read()
        if ret:
            frame = cv2.resize(frame, FRAME_SIZE)
            # Apply thermal fusion color
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            thermal_colored = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
            with thermal_lock:
                thermal_frame = thermal_colored.copy()
            out_thermal.write(thermal_colored)
        else:
            time.sleep(0.05)
    print("🌡️ Thermal thread stopped.")
    thermalCapture.release()
    out_thermal.release()

if thermal_available:
    t_thermal = threading.Thread(target=thermal_loop, daemon=True)
    t_thermal.start()

# ------------------------------------------------------------
# MAIN LOOP – YOLO inference + recording
# ------------------------------------------------------------
print("🎥 Monitoring started. Press Ctrl+C to stop.")
try:
    while True:
        # Capture from visual camera
        frame_visual = visualCapture.capture_array()
        frame_visual_rgb = cv2.cvtColor(frame_visual, cv2.COLOR_RGBA2BGR)

        # Run inference on visual camera
        try:
            results = visual_model.predict(frame_visual_rgb)
            overlay_visual = (
                results.image_overlay()
                if callable(results.image_overlay)
                else results.image_overlay
            )
        except Exception as e:
            print(f"⚠️ Inference error: {e}")
            overlay_visual = frame_visual_rgb

        out_visual.write(overlay_visual)

        # Combine both frames side by side
        with thermal_lock:
            combined = np.hstack((overlay_visual, thermal_frame))
        out_combined.write(combined)

        # Rotate videos every SAVE_INTERVAL seconds
        if time.time() - last_save_time > SAVE_INTERVAL:
            out_visual.release()
            out_thermal.release()
            out_combined.release()
            out_visual, out_thermal, out_combined = create_video_writers()
            last_save_time = time.time()

        # Control frame rate
        time.sleep(1 / FPS)

except KeyboardInterrupt:
    print("🛑 Stopping monitoring...")

finally:
    thermal_running = False
    if thermal_available:
        t_thermal.join()
    visualCapture.stop()
    out_visual.release()
    out_combined.release()
    cv2.destroyAllWindows()
    print("✅ Session complete.")
    print(f"📂 All videos saved under: {SESSION_DIR}")
