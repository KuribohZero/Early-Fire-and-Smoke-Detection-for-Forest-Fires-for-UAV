# device.py
import asyncio
import json
import paho.mqtt.client as mqtt
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

client_id = "raspberryPi"
broker_url = "test.mosquitto.org"

pc = RTCPeerConnection()
dc = pc.createDataChannel("deviceChannel")

# Handle messages from laptop
@dc.on("message")
def on_message(message):
    print(f"[Pi] Received command: {message}")
    dc.send(f"Pi received: {message}")

@dc.on("open")
def on_open():
    print("[Pi] DataChannel open and ready for messages")

# MQTT setup
client = mqtt.Client(client_id)

def publish_signal(type_, payload):
    msg = json.dumps({type_: payload})
    client.publish("webrtc/laptop/signal", msg)

def on_message_mqtt(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    asyncio.run(handle_signal(data))

async def handle_signal(data):
    if "sdp" in data:
        print("[Pi] Received SDP")
        sdp = data["sdp"]
        desc = RTCSessionDescription(sdp["sdp"], sdp["type"])
        await pc.setRemoteDescription(desc)

        if desc.type == "offer":
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            publish_signal("sdp", {"sdp": answer.sdp, "type": answer.type})

    if "candidate" in data:
        print("[Pi] Received ICE candidate")
        c = data["candidate"]
        candidate = RTCIceCandidate(c["candidate"], c["sdpMid"], c["sdpMLineIndex"])
        await pc.addIceCandidate(candidate)

@pc.on("icecandidate")
def on_icecandidate(event):
    if event.candidate:
        publish_signal("candidate", {
            "candidate": event.candidate.candidate,
            "sdpMid": event.candidate.sdpMid,
            "sdpMLineIndex": event.candidate.sdpMLineIndex
        })

# Start MQTT
client.on_message = on_message_mqtt
client.connect(broker_url, 1883)
client.subscribe("webrtc/raspberryPi/#")
client.loop_start()

print("[Pi] Waiting for signaling...")
asyncio.get_event_loop().run_forever()
