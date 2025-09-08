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
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "alerts": alerts})

@app.post("/decision")
def decision(alert_id: int = Form(...), action: str = Form(...)):
    # Update local status
    for alert in alerts:
        if alert["id"] == alert_id:
            alert["status"] = action

            # Publish decision back to Pi
            payload = {
                "id": alert_id,
                "decision": action,
                "timestamp": datetime.now().isoformat()
            }
            client = mqtt.Client()
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.publish(MQTT_TOPIC_RESPONSE, json.dumps(payload))
            client.disconnect()

    return {"status": "ok", "alert_id": alert_id, "action": action}