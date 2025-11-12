#!/usr/bin/env python3
# ---------------- main_with_mavlink.py ----------------
# Dual-camera recorder with:
# - visual + thermal inference
# - thermal fusion colouring
# - HUD overlay (fps / detections / timestamp)
# - rotating AVI files every SAVE_INTERVAL
# - live preview
# - periodic MAVLink+console status
# - all messages go through Logger

import cv2
import os
import time
from datetime import datetime
from picamera2 import Picamera2

from config import (
    make_session_dir, FRAME_SIZE, COMBINED_SIZE, THERMAL_DEVICE,
    CAMERA_WARMUP, FPS, FOURCC, SAVE_INTERVAL, STATUS_INTERVAL,
    VISUAL_MODEL_NAME, THERMAL_MODEL_NAME, ZOO_URL,
    MAVLINK_DEVICE, MAVLINK_BAUD, MAVLINK_SEVERITY_INFO
)
from vision import VisualPipeline, ThermalWorker
from mavlink_utils import MavLinkClient, Logger


def create_writers(session_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    v_path = os.path.join(session_dir, f"visual_{ts}.avi")
    t_path = os.path.join(session_dir, f"thermal_{ts}.avi")
    c_path = os.path.join(session_dir, f"combined_{ts}.avi")
    out_v = cv2.VideoWriter(v_path, FOURCC, FPS, FRAME_SIZE)
    out_t = cv2.VideoWriter(t_path, FOURCC, FPS, FRAME_SIZE)
    out_c = cv2.VideoWriter(c_path, FOURCC, FPS, COMBINED_SIZE)
    return out_v, out_t, out_c, ts


def draw_hud(img, fps, frame_num, dets):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hud = f"Time: {ts} | Frame: {frame_num} | FPS: {fps:.1f} | Detections: {dets}"
    cv2.putText(
        img,
        hud,
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return img, hud


def main():
    # --------------------------------------------------
    # Startup: session dir + mavlink + logger
    # --------------------------------------------------
    session_dir = make_session_dir()

    mav = MavLinkClient(MAVLINK_DEVICE, MAVLINK_BAUD, MAVLINK_SEVERITY_INFO)
    try:
        mav.connect()
    except Exception as e:
        # if mavlink fails, we still keep running — mav=None
        mav = None

    log = Logger(mav)

    log.info(f"💾 Session: {session_dir}")
    log.info("Booting vision pipelines...")

    # --------------------------------------------------
    # Init pipelines (visual + thermal)
    # --------------------------------------------------
    visual = VisualPipeline(VISUAL_MODEL_NAME, ZOO_URL, FRAME_SIZE)
    thermal = ThermalWorker(THERMAL_DEVICE, THERMAL_MODEL_NAME, ZOO_URL, FRAME_SIZE)

    # load models
    try:
        visual.init_model()
        log.info("Visual model loaded.")
    except Exception as e:
        log.error(f"Visual model init fail: {e}")
        return

    try:
        thermal.init()
        log.info("Thermal model loaded.")
    except Exception as e:
        log.error(f"Thermal model init fail: {e}")
        return

    # init cameras
    try:
        visual.init_camera(Picamera2)
        log.info("Visual camera initialized.")
    except Exception as e:
        log.error(f"Visual camera error: {e}")
        return

    # thermal.init() already opened cv2.VideoCapture(...) above

    # --------------------------------------------------
    # Warmup
    # --------------------------------------------------
    log.info(f"Warming cameras {CAMERA_WARMUP}s")
    time.sleep(CAMERA_WARMUP)

    # --------------------------------------------------
    # Start writers + thermal thread
    # --------------------------------------------------
    out_visual, out_thermal, out_combined, seg_stamp = create_writers(session_dir)
    log.info(f"🎞️ New segment: {seg_stamp}")

    thermal.start(out_writer=out_thermal)
    log.info("Recording started")

    # --------------------------------------------------
    # Loop state
    # --------------------------------------------------
    frame_count_total = 0            # total frames since boot
    det_count_window = 0             # detection counter for STATUS_INTERVAL
    last_rotate = time.time()
    last_report = time.time()

    fps_window_frames = 0
    fps_window_start = time.time()

    try:
        while True:
            loop_start = time.time()

            # ---- VISUAL PIPELINE ----
            overlay_v, dets_v = visual.capture_and_infer()
            out_visual.write(overlay_v)
            frame_count_total += 1
            det_count_window += dets_v

            # ---- THERMAL PIPELINE (already running in thread) ----
            overlay_t = thermal.latest_frame()

            # ---- COMBINE ----
            combined = cv2.hconcat([overlay_v, overlay_t])

            # ---- FPS CALC ----
            fps_window_frames += 1
            elapsed_fps = time.time() - fps_window_start
            fps_now = fps_window_frames / elapsed_fps if elapsed_fps > 0 else 0.0

            # ---- HUD ----
            combined_hud, hud_text = draw_hud(
                combined,
                fps_now,
                frame_count_total,
                det_count_window,
            )

            out_combined.write(combined_hud)

            # ---- PREVIEW ----
            cv2.imshow("Visual + Thermal Preview", combined_hud)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                log.info("Quit requested by user (q)")
                break

            # ---- ROTATE FILES EVERY SAVE_INTERVAL ----
            if time.time() - last_rotate >= SAVE_INTERVAL:
                out_visual.release()
                out_thermal.release()
                out_combined.release()

                out_visual, out_thermal, out_combined, seg_stamp = create_writers(session_dir)
                log.info(f"🎞️ New segment: {seg_stamp}")
                last_rotate = time.time()

                # reset FPS window on new segment
                fps_window_frames = 0
                fps_window_start = time.time()

            # ---- STATUS EVERY STATUS_INTERVAL (30s) ----
            if time.time() - last_report >= STATUS_INTERVAL:
                # log hud_text too so GCS sees same overlay info
                log.info(f"[Status] {hud_text}")
                last_report = time.time()
                det_count_window = 0  # reset detection counter for next window

                # OPTIONAL: send snapshot to GCS
                # if mav:
                #     mav.send_jpeg(combined_hud, label="combined preview")

            # keep ~target FPS
            loop_time = time.time() - loop_start
            sleep_t = max(0, (1.0 / FPS) - loop_time)
            time.sleep(sleep_t)

    except KeyboardInterrupt:
        log.warn("KeyboardInterrupt -> stopping vision")

    finally:
        # stop threads / release HW
        thermal.stop()
        visual.stop()

        out_visual.release()
        out_thermal.release()
        out_combined.release()

        cv2.destroyAllWindows()

        log.info("Vision stopped")
        log.info(f"Files saved in: {session_dir}")


if __name__ == "__main__":
    main()
