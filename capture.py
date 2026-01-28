"""
Webcam capture module with threaded frame acquisition
"""
import cv2
import threading
import queue
import time
from dataclasses import dataclass
import numpy as np
from typing import Optional
import config


@dataclass
class FrameData:
    """Container for frame data passed through queue"""
    frame: np.ndarray
    timestamp: float
    frame_id: int
    mirrored: np.ndarray


class WebcamCapture:
    """Handles webcam capture in a separate thread for minimal latency"""

    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.cap = None
        self.frame_id = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

    def initialize_camera(self) -> bool:
        """Initialize webcam with optimal settings"""
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            return False

        # Set resolution
        width, height = config.CAPTURE["resolution"]
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Set FPS
        self.cap.set(cv2.CAP_PROP_FPS, config.CAPTURE["fps_target"])

        # Disable autofocus for stability (if supported)
        try:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        except:
            pass  # Not all cameras support this

        return True

    def capture_loop(self):
        """Main capture loop - runs in separate thread"""
        while self.shared_state.is_running.is_set():
            if self.shared_state.is_paused.is_set():
                time.sleep(0.1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue

            # Create frame data
            timestamp = time.perf_counter()
            mirrored = cv2.flip(frame, 1)  # Mirror for display

            frame_data = FrameData(
                frame=frame,
                timestamp=timestamp,
                frame_id=self.frame_id,
                mirrored=mirrored
            )

            # Non-blocking put - drop old frames if queue is full
            try:
                self.shared_state.frame_queue.put_nowait(frame_data)
            except queue.Full:
                # Drop old frame and try again
                try:
                    self.shared_state.frame_queue.get_nowait()
                    self.shared_state.frame_queue.put_nowait(frame_data)
                except:
                    pass

            self.frame_id += 1
            self._update_fps()

    def _update_fps(self):
        """Calculate current FPS"""
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()

    def release(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
