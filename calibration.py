"""
Calibration system for establishing user's neutral pose baseline
"""
import time
import math
from typing import List, Tuple
import config
from dataclasses import dataclass, field
from utils import calculate_distance


@dataclass
class CalibrationData:
    """Stores calibration baseline data"""
    neutral_torso_angle: float = 0.0
    shoulder_width: float = 0.0
    torso_length: float = 0.0
    neutral_hip_height: float = 0.0
    wrist_neutral_z: float = 0.0
    is_calibrated: bool = False
    calibration_frames: List[dict] = field(default_factory=list)


class CalibrationSystem:
    """Handles T-pose calibration workflow"""

    def __init__(self):
        self.duration = config.TIMING["calibration_duration"]
        self.start_time = None
        self.calibration_data = CalibrationData()

    def start_calibration(self):
        """Begin calibration process"""
        self.start_time = time.time()
        self.calibration_data.calibration_frames = []
        print("\n" + "="*50)
        print("CALIBRATION STARTED")
        print("="*50)
        print("Please stand in a T-pose:")
        print("  - Feet shoulder-width apart")
        print("  - Arms extended horizontally to the sides")
        print("  - Stand straight, facing the camera")
        print("  - Hold steady for 3 seconds...")
        print()

    def update(self, landmarks: dict) -> Tuple[bool, float]:
        """
        Update calibration with new frame
        Returns: (is_complete, progress_ratio)
        """
        if self.start_time is None:
            return False, 0.0

        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)

        # Collect frame
        self.calibration_data.calibration_frames.append(landmarks)

        # Check if complete
        if elapsed >= self.duration:
            self._finalize_calibration()
            return True, 1.0

        return False, progress

    def _finalize_calibration(self):
        """Calculate calibration values from collected frames"""
        frames = self.calibration_data.calibration_frames

        if len(frames) == 0:
            print("Calibration failed: no frames collected")
            return

        # Calculate averages from middle 80% of frames (discard outliers)
        start_idx = len(frames) // 10
        end_idx = len(frames) - start_idx
        valid_frames = frames[start_idx:end_idx]

        if len(valid_frames) == 0:
            valid_frames = frames

        # Calculate neutral torso angle
        angles = []
        shoulder_widths = []
        torso_lengths = []
        hip_heights = []
        wrist_z_values = []

        for frame in valid_frames:
            # Torso angle
            hip_center_x = (frame['left_hip'][0] + frame['right_hip'][0]) / 2
            shoulder_center_x = (frame['left_shoulder'][0] + frame['right_shoulder'][0]) / 2
            hip_center_y = (frame['left_hip'][1] + frame['right_hip'][1]) / 2
            shoulder_center_y = (frame['left_shoulder'][1] + frame['right_shoulder'][1]) / 2

            dx = shoulder_center_x - hip_center_x
            dy = shoulder_center_y - hip_center_y
            angle = math.degrees(math.atan2(dx, dy))
            angles.append(angle)

            # Shoulder width
            shoulder_width = calculate_distance(
                (frame['left_shoulder'][0], frame['left_shoulder'][1]),
                (frame['right_shoulder'][0], frame['right_shoulder'][1])
            )
            shoulder_widths.append(shoulder_width)

            # Torso length
            torso_length = calculate_distance(
                (shoulder_center_x, shoulder_center_y),
                (hip_center_x, hip_center_y)
            )
            torso_lengths.append(torso_length)

            # Hip height
            hip_heights.append(hip_center_y)

            # Wrist neutral depth
            wrist_z = (frame['left_wrist'][2] + frame['right_wrist'][2]) / 2
            wrist_z_values.append(wrist_z)

        # Set calibration values
        self.calibration_data.neutral_torso_angle = sum(angles) / len(angles)
        self.calibration_data.shoulder_width = sum(shoulder_widths) / len(shoulder_widths)
        self.calibration_data.torso_length = sum(torso_lengths) / len(torso_lengths)
        self.calibration_data.neutral_hip_height = sum(hip_heights) / len(hip_heights)
        self.calibration_data.wrist_neutral_z = sum(wrist_z_values) / len(wrist_z_values)
        self.calibration_data.is_calibrated = True

        print("\n" + "="*50)
        print("CALIBRATION COMPLETE!")
        print("="*50)
        print(f"Neutral torso angle: {self.calibration_data.neutral_torso_angle:.2f}°")
        print(f"Shoulder width:      {self.calibration_data.shoulder_width:.3f}")
        print(f"Torso length:        {self.calibration_data.torso_length:.3f}")
        print(f"Starting gesture recognition...")
        print("="*50)
        print()
