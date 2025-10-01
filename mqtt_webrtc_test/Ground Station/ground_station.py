# laptop.py
import asyncio
import json
import paho.mqtt.client as mqtt
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

client_id = "laptop"
broker_url = "test.mosquitto.org"

pc = RTCPeerConnection()
dc = None

def publish_signal(type_, payload):
    msg = json.dumps({type_: payload})
    client.publish("webrtc/raspberryPi/signal", msg)

async def create_offer():
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    publish_signal("sdp", {"sdp": offer.sdp, "type": offer.type})

def on_message_mqtt(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    asyncio.run(handle_signal(data))

async def handle_signal(data):
    if "sdp" in data:
        print("[Laptop] Received SDP")
        sdp = data["sdp"]
        desc = RTCSessionDescription(sdp["sdp"], sdp["type"])
        await pc.setRemoteDescription(desc)

    if "candidate" in data:
        print("[Laptop] Received ICE candidate")
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

@pc.on("datachannel")
def on_datachannel(channel):
    global dc
    dc = channel

    @dc.on("open")
    def on_open():
        print("[Laptop] DataChannel open! Sending command...")
        dc.send("Hello Pi, start streaming!")

    @dc.on("message")
    def on_message(message):
        print(f"[Laptop] Received from Pi: {message}")

# Start MQTT
client = mqtt.Client(client_id)
client.on_message = on_message_mqtt
client.connect(broker_url, 1883)
client.subscribe("webrtc/laptop/#")
client.loop_start()

print("[Laptop] Sending offer...")
asyncio.get_event_loop().run_until_complete(create_offer())
asyncio.get_event_loop().run_forever()
