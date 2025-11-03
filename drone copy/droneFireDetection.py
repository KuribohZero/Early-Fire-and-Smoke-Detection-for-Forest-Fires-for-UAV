# camera_module.py
import cv2
import os
import time
from picamera2 import Picamera2

#----------------------------------------------#
def mav_send_status(connection, text, severity=6):
    connection.mav.statustext_send(severity, text.encode('utf-8'))
    print(f"📡 MAV: {text}")

#----------------------------------------------#
def send_image_via_mavlink(connection, image_path):
    """Send a JPEG image via MAVLink as chunks."""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    img_size = len(img_data)
    connection.mav.data_transmission_handshake_send(
        0, img_size, 640, 480, 0, 0, int(img_size / 253) + 1, 253
    )
    seq = 0
    for i in range(0, img_size, 253):
        chunk = img_data[i:i + 253]
        connection.mav.encapsulated_data_send(seq, chunk)
        seq += 1
    mav_send_status(connection, "🔥 Fire image sent to GCS!")

#----------------------------------------------#
def start_camera_recording(connection, visual_model):
    """Handles visual camera capture, fire detection, and alert logic."""
    visual_available = False
    try:
        info = Picamera2.global_camera_info()
        if info:
            visual_available = True
            visualCapture = Picamera2()
            config = visualCapture.create_video_configuration(main={"size": (640, 480)})
            visualCapture.configure(config)
            visualCapture.start()
            time.sleep(2)
            print("📷 Visual camera initialized.")
        else:
            print("No Visual Camera found.")
    except Exception as e:
        print(f"Error initializing visual camera: {e}")

    if not visual_available:
        mav_send_status(connection, "❌ No visual camera available.")
        return

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out_visual = cv2.VideoWriter('visual_fire_detection.avi', fourcc, 20.0, (640, 480))

    # Fire detection tracking
    fire_detected = False
    fire_start_time = None
    fire_alert_sent = False
    fire_hold_duration = 5  # seconds

    #----------------------------------------------#
    while visual_available:
        frame_visual = visualCapture.capture_array()
        frame_visual_rgb = cv2.cvtColor(frame_visual, cv2.COLOR_RGB
