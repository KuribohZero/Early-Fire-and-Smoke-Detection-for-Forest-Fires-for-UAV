# ---------------- mavlink_utils.py ----------------
from pymavlink import mavutil
from datetime import datetime
import cv2

class MavLinkClient:
    def __init__(self, device, baud, severity_default=6):
        self.dev = device
        self.baud = baud
        self.severity = severity_default
        self.link = None

    def connect(self):
        self.link = mavutil.mavlink_connection(self.dev, baud=self.baud)
        # wait for heartbeat so we know FC is alive
        self.link.wait_heartbeat(timeout=10)
        self.send_text("MAVLink connected")

    def send_text(self, text, severity=None):
        if self.link is None:
            return
        sev = self.severity if severity is None else severity
        # MAVLink wants bytes
        self.link.mav.statustext_send(sev, text.encode("utf-8"))

    def send_jpeg(self, image_bgr, label="snapshot"):
        """
        Send a JPEG image to GCS via MAVLink using DATA_TRANSMISSION_HANDSHAKE
        and ENCAPSULATED_DATA.
        """
        if self.link is None or image_bgr is None:
            return

        ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            self.send_text("Failed to encode JPEG")
            return

        img = buf.tobytes()
        img_size = len(img)

        # Announce image transfer
        self.link.mav.data_transmission_handshake_send(
            0,                      # type (0 = JPG)
            img_size,               # size
            image_bgr.shape[1],     # width
            image_bgr.shape[0],     # height
            0, 0,                   # packets, payload size legacy fields
            (img_size // 253) + 1,  # number of chunks
            253                     # chunk size
        )

        # Send chunks
        seq = 0
        for i in range(0, img_size, 253):
            chunk = img[i:i+253]
            self.link.mav.encapsulated_data_send(seq, chunk)
            seq += 1

        ts = datetime.now().strftime("%H:%M:%S")
        self.send_text(f"Sent {label} ({img_size//1024} KB) at {ts}")


class Logger:
    """
    Small helper so we only call logger.info() instead of print() or mav.send_text() everywhere.
    If mavlink is available, messages go out over MAVLink AND console.
    If mavlink is missing, they just print().
    """
    def __init__(self, mav_client: MavLinkClient | None):
        self.mav = mav_client

    def info(self, msg: str):
        # console
        print(msg)
        # mavlink
        if self.mav is not None:
            # truncate to something safe-ish for statustext (50 chars is typical GCS display)
            short = msg[:50]
            self.mav.send_text(short)

    def warn(self, msg: str):
        warn_msg = f"⚠️ {msg}"
        print(warn_msg)
        if self.mav is not None:
            short = warn_msg[:50]
            # MAVLink severity 4 ~ warning-ish
            self.mav.send_text(short, severity=4)

    def error(self, msg: str):
        err_msg = f"❌ {msg}"
        print(err_msg)
        if self.mav is not None:
            short = err_msg[:50]
            # MAVLink severity 3 ~ error-ish
            self.mav.send_text(short, severity=3)
