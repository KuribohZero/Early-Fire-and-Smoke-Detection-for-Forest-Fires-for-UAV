import base64
import json
import threading
from datetime import datetime
from typing import List

#Image processing imports
import cv2
import numpy as np
#import picamera2
import time

#For importing hailo model
import degirum as dg

#Communication Imports for FAST API and MQTT
import paho.mqtt.client as mqtt
import asyncio
from starlette.websockets import WebSocketState
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

 
#Configuration
#Configure the pat
BASE_DIR = Path(__file__).resolve().parent

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
#Configure MQTT
MQTT_BROKER =  "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_ALERT = "fire_detection/alerts"
MQTT_TOPIC_RESPONSE = "fire_detection/responses"

alerts = []

#MQTT Subscriber
def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"[MQTT] Received alert: {data['timestamp']}")

    alerts.append({
        "id": len(alerts) + 1,
        "timestamp": data["timestamp"],
        "gps": data["gps"],
        "mode": data["mode"],
        "image": data["image"],  # base64 string
        "status": "pending"
    })

def mqtt_loop():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC_ALERT)
    client.loop_start()
    return client

# Start MQTT in a background thread
threading.Thread(target=mqtt_loop, daemon=True).start()


#FastAPI Setup
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount(
    "/static", 
    StaticFiles(directory=str(BASE_DIR / "static")), 
    name="static",
)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# WebSocket endpoint for real-time video streaming with FPS
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Initialize camera
    cap = cv2.VideoCapture(0)

    # Check that the camera is accessible
    # Code from : https://chatgpt.com/share/683867a8-db8c-800e-ae13-1b2fcdfee4ee
    if not cap.isOpened():
        print("⚠️  No camera detected!")
        # Reject WebSocket with proper close code
        await websocket.close(code=1003)  # 1003 = unsupported data 
        return

    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    prev_frame_time = time.time()

    # Accept the WebSocket connection
    await websocket.accept()

    try:
        while True:
            # Read a frame from the camera in a background thread
            # Code from: https://chatgpt.com/share/683867a8-db8c-800e-ae13-1b2fcdfee4ee
            # off-load the heavy work, keep the server responsive, get the result when it’s ready
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                break  # Stop if the camera failed

            # Run inference on the frame (also off the main async thread)
            # off-load the heavy work, keep the server responsive, get the result when it’s ready
            inf = await asyncio.to_thread(visual_model, frame)
            frm = inf.image_overlay

            # Calculate and draw FPS on the frame
            #  Get the current time
            now = time.time()
            # Compute the FPS (Frames Per Second)
            # 1) (now - prev_frame_time) = time elapsed between two frames (seconds)
            # 2) 1 / elapsed_time = number of frames processed per second
            fps = 1 / (now - prev_frame_time)
            # Store the current time for the next iteration
            prev_frame_time = now
            # Draw the FPS value on the image
            cv2.putText(frm, f"FPS: {fps:.0f}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0), 2, cv2.LINE_AA)

            # Code from: https://chatgpt.com/share/68383000-066c-800e-8ae4-a21eb074307d
            # Encode the annotated frame as JPEG
            success, jpg = cv2.imencode('.jpg', frm)
            if not success:
                continue  # Skip this frame if encoding fails

            # Try to send the JPEG over WebSocket
            # Code from: https://chatgpt.com/share/68383000-066c-800e-8ae4-a21eb074307d
            try:
                await websocket.send_bytes(jpg.tobytes())
            except Exception:
                # If the client disconnected or network error → exit loop
                print("Send stopped (client disconnected?)")
                break

    finally:
        # Always release the camera
        cap.release()

        # Gracefully close the WebSocket if it's still open
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close()