#Image processing imports
import cv2
import numpy as np
#import picamera2
import time

#For importing hailo model
import degirum as dg, degirum_tools

# Initialize video captures for visual and thermal cameras
"""
visualCapture =picamera2()
config = visualCapture.create_still_configuration(main={"size": (640, 480)})
visualCapture.configure(config)
visualCapture.start()
"""
"""
thermalCapture =cv2.VideoCapture('/dev/video0')
thermalCapture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
thermalCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

time.sleep(2)  # Allow cameras to warm up
"""
# Load models for visual and thermal cameras

visual_model = dg.load_model(
    model_name="yolov11n",
    inference_host_address="@local",
    zoo_url=str(BASE_DIR / "hailo_model"),
    token="",
    device_type="HAILORT/HAILO8L",
)

"""
thermal_model = dg.load_model(
    model_name="yolov11n", # Model name
    inference_host_address="@local",
    zoo_url="hailo_model", # link to the custom model folder
    token="",
    device_type="HAILORT/HAILO8L",
)
"""
