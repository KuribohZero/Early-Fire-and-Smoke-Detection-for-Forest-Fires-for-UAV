# ---------------- vision.py ----------------
import cv2
import time
import threading
import numpy as np
from datetime import datetime
import degirum as dg

class VisualPipeline:
    def __init__(self, model_name, zoo_url, frame_size):
        self.model_name = model_name
        self.zoo_url = zoo_url
        self.frame_size = frame_size
        self.model = None
        self.picam = None

    def init_model(self):
        host = dg.connect(inference_host_address="@local", zoo_url=self.zoo_url)
        self.model = dg.load_model(
            model_name=self.model_name,
            inference_host_address="@local",
            zoo_url=self.zoo_url,
            overlay_show_probabilities=True
        )

    def init_camera(self, Picamera2):
        self.picam = Picamera2()
        cfg = self.picam.create_video_configuration(main={"size": self.frame_size})
        self.picam.configure(cfg)
        self.picam.start()

    def capture_and_infer(self):
        """Returns (overlay_bgr, detections_count)."""
        frame = self.picam.capture_array()                  # RGBA
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        try:
            res = self.model.predict(bgr)
            overlay = res.image_overlay() if callable(res.image_overlay) else res.image_overlay
            dets = len(getattr(res, "detections", []) or [])
        except Exception as e:
            print(f"⚠️ Visual inference error: {e}")
            overlay = bgr
            dets = 0
        return overlay, dets

    def stop(self):
        if self.picam:
            self.picam.stop()

class ThermalWorker:
    def __init__(self, device_path, model_name, zoo_url, frame_size):
        self.dev = device_path
        self.model_name = model_name
        self.zoo_url = zoo_url
        self.frame_size = frame_size

        self.cap = None
        self.model = None

        self.frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def init(self):
        self.cap = cv2.VideoCapture(self.dev, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])

        host = dg.connect(inference_host_address="@local", zoo_url=self.zoo_url)
        self.model = dg.load_model(
            model_name=self.model_name,
            inference_host_address="@local",
            zoo_url=self.zoo_url,
            overlay_show_probabilities=True
        )

    def start(self, out_writer):
        self.running = True
        self.thread = threading.Thread(target=self._loop, args=(out_writer,), daemon=True)
        self.thread.start()

    def _loop(self, out_writer):
        print("🧵 Thermal thread started")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # fusion colour
            frame = cv2.resize(frame, self.frame_size)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            thermal_colored = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)

            try:
                res = self.model.predict(thermal_colored)
                overlay = res.image_overlay() if callable(res.image_overlay) else res.image_overlay
            except Exception as e:
                print(f"⚠️ Thermal inference error: {e}")
                overlay = thermal_colored

            with self.lock:
                self.frame = overlay.copy()

            if out_writer is not None:
                out_writer.write(overlay)

        print("🌡️ Thermal thread stopping")
        if self.cap:
            self.cap.release()

    def latest_frame(self):
        with self.lock:
            return self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
