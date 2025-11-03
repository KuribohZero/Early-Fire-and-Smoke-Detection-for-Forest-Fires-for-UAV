import cv2
from pymavlink import mavutil

# === MAVLink Setup ===
connection = mavutil.mavlink_connection('/dev/ttyAMA0', baud=57600)  # or UDP link
def mav_send_status(text, severity=6):
    connection.mav.statustext_send(severity, text.encode('utf-8'))
    print("📡 MAV:", text)

# === Image send helper ===
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

