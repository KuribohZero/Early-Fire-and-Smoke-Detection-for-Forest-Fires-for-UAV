# main.py
import time
from pymavlink import mavutil
import degirum as dg
from camera_module import start_camera_recording

#----------------------------------------------#
# MAVLink Setup
def mav_send_status(connection, text, severity=6):
    connection.mav.statustext_send(severity, text.encode('utf-8'))
    print(f"📡 MAV: {text}")

print("🔌 Connecting to MAVLink...")
connection = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)
connection.wait_heartbeat()
print(f"✅ MAVLink connected to system (sysid={connection.target_system}, compid={connection.target_component})")

mav_send_status(connection, "MAVLink connected, initializing Hailo model...")

#----------------------------------------------#
# Hailo Model Setup
try:
    inference_host = dg.connect(inference_host_address="@local", zoo_url="model_zoo")
    model_list = inference_host.list_models(device_type="HAILORT/HAILO8L")

    if not model_list:
        print("❌ No models found on device. Exiting.")
        exit(1)

    print(f"✅ Models available: {model_list}")

    visual_model = dg.load_model(
        model_name="yolov11n_rgb--640x640",
        inference_host_address="@local",
        zoo_url="model_zoo",
        overlay_show_probabilties=True
    )

    mav_send_status(connection, "✅ Visual detection model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading Hailo model: {e}")
    exit(1)

#----------------------------------------------#
# Start camera capture after MAVLink is ready
try:
    mav_send_status(connection, "🎥 Starting visual camera capture...")
    start_camera_recording(connection, visual_model)
except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")
    mav_send_status(connection, "Camera capture stopped by user.")
except Exception as e:
    print(f"❌ Camera module error: {e}")
    mav_send_status(connection, f"Camera module error: {e}")
