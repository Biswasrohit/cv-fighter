"""
Pose detection module using MediaPipe Tasks API
"""
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import time
import os
import urllib.request
from typing import Optional, Tuple
import config

# Model download URL
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker.task")


def download_model():
    """Download the pose landmarker model if it doesn't exist"""
    if not os.path.exists(MODEL_PATH):
        print("Downloading pose landmarker model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded successfully!")


class PoseDetector:
    """Wrapper for MediaPipe pose detection using Tasks API"""

    # Landmark indices for the body parts we need
    LANDMARK_INDICES = {
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28,
    }

    def __init__(self):
        # Ensure model is downloaded
        download_model()

        # Create pose landmarker options
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=config.MEDIAPIPE["min_detection_confidence"],
            min_pose_presence_confidence=config.MEDIAPIPE["min_detection_confidence"],
            min_tracking_confidence=config.MEDIAPIPE["min_tracking_confidence"],
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0

        # For drawing landmarks
        self._connections = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Arms
            (11, 23), (12, 24), (23, 24),  # Torso
            (23, 25), (25, 27), (24, 26), (26, 28),  # Legs
        ]

    def detect(self, frame) -> Tuple[Optional[dict], Optional[object]]:
        """
        Detect pose in frame
        Returns: (landmarks_dict, results) or (None, None) if no pose detected
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Increment timestamp (MediaPipe requires monotonically increasing timestamps)
        self._frame_timestamp_ms += 33  # ~30fps

        # Process frame
        results = self.landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            # Extract landmarks to our custom format
            landmarks = self._extract_landmarks(results.pose_landmarks[0])
            return landmarks, results

        return None, None

    def _extract_landmarks(self, pose_landmarks) -> dict:
        """Extract relevant landmarks into a dictionary"""
        landmarks = {}
        for name, idx in self.LANDMARK_INDICES.items():
            lm = pose_landmarks[idx]
            landmarks[name] = (lm.x, lm.y, lm.z, lm.visibility)
        landmarks['timestamp'] = time.perf_counter()
        return landmarks

    def draw_landmarks(self, frame, results):
        """Draw pose landmarks on frame"""
        if results and results.pose_landmarks and len(results.pose_landmarks) > 0:
            pose_landmarks = results.pose_landmarks[0]
            h, w = frame.shape[:2]

            # Draw connections
            for start_idx, end_idx in self._connections:
                start = pose_landmarks[start_idx]
                end = pose_landmarks[end_idx]

                if start.visibility > 0.5 and end.visibility > 0.5:
                    start_point = (int(start.x * w), int(start.y * h))
                    end_point = (int(end.x * w), int(end.y * h))
                    cv2.line(frame, start_point, end_point, (255, 255, 255), 2)

            # Draw landmarks
            for idx in self.LANDMARK_INDICES.values():
                lm = pose_landmarks[idx]
                if lm.visibility > 0.5:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

    def close(self):
        """Clean up resources"""
        self.landmarker.close()
