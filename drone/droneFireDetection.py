#Image processing imports
import cv2
import numpy as np
from picamera2 import Picamera2
import os
import time
#For importing hailo model
import degirum as dg
from pymavlink import mavutil

#----------------------------------------------#
#MAVLink Setup
connection = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)  # or UDP link
def mav_send_status(text, severity=6):
    connection.mav.statustext_send(severity, text.encode('utf-8'))
    print("📡 MAV:", text)

#----------------------------------------------#
#Hailo Model Setup
#Check models are available in the zoo_url location

visual_Camera_Check = dg.connect(
    inference_host_address="@local",
    zoo_url="model_zoo",
)

#Check models are availabe
model_list = inference_manager.list_models(device_type="HAILORT/HAILO8L")
if model_list == []:
    print("No models found on the device.")
    exit(1)
else:
    print(f"Models found: {model_list}")

#load visual and thermal model
visual_model = dg.load_model(
    model_name="yolov11n_rgb--640x640",
    inference_host_address="@local",
    zoo_url="model_zoo",
    overlay_show_probabilties=True
)


thermal_model = dg.load_model(
    model_name="yolov11n", # Model name
    inference_host_address="@local",
    zoo_url="hailo_model",
    overlay_show_probabilties=True
)

#----------------------------------------------#
#Check Camera Availability
visualCameraAvability = False
try:
    info = Picamera2.global_camera_info()
    if info:
        visualCameraAvability = True
        visualCapture = Picamera2()
        config = visualCapture.create_still_configuration(main={"size": (640, 480)})
        visualCapture.configure(config)
        visualCapture.start()
        time.sleep(2)  # Allow camera to warm up
        print("Visual Camera is initialised.")
    else:
        print("No Visual Camera found.")
except Exception as e:
    print(f"Error initializing Visual Camera: {e}")

#Check Thermal Camera Availability
thermalCameraAvability = False
thermal_device = "/device/video8"

if os.path.exists(thermal_device):
    thermalCapture = cv2.VideoCapture(thermal_device, cv2.CAP_V4L2)
    thermalCapture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    thermalCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(2)  # Allow camera to warm up
    if thermalCapture.isOpened():
        thermalCameraAvability = True
        print("Thermal Camera is initialised.")
    else:
        print(f"Failed to open Thermal Camera at {thermal_device}.")
else:
    print(f"Thermal Camera device {thermal_device} does not exist.")

if not (visualCameraAvability or thermalCameraAvability):
    print("No cameras available. Exiting.")
    exit(1)

#----------------------------------------------#
#Image send helper
def send_image_via_mavlink(connection, image_path):
    """Send a JPEG image file via MAVLink as chunks."""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    img_size = len(img_data)

    # Notify GCS of an incoming image
    connection.mav.data_transmission_handshake_send(
        0,  # type (0 = jpg)
        img_size,
        640, 480,
        0, 0,
        int(img_size / 253) + 1,
        253
    )

    # Send chunks of 253 bytes
    seq = 0
    for i in range(0, img_size, 253):
        chunk = img_data[i:i+253]
        connection.mav.encapsulated_data_send(seq, chunk)
        seq += 1

    mav_send_status("🔥 Fire image sent to GCS!")
        
#----------------------------------------------#
#Visual Camera Fire Detection Function
#Detect fire and smoke using model on visual camera
#If fire or smoke detected save image of frame with boundary box
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out_visual = cv2.VideoWriter('visual_fire_detection.avi', fourcc, 20.0, (640, 480))

while True:
    frame_visual = visualCapture.capture_array()

    frame_visual_rgb = cv2.cvtColor(frame_visual, cv2.COLOR_RGBA2BGR)

    #Run inference on visual model
    results_visual = visual_model.predict(frame_visual_rgb)

    overlay_visual = results_visual.image_overlay() if callable(results_visual.image_overlay) else results_visual.image_overlay
    cv2.imshow("Visual Fire Detection", overlay_visual)

    out_visual.write(overlay_visual)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


visualCapture.stop()
cv2.destroyAllWindows()

#----------------------------------------------#