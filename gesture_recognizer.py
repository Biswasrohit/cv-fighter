"""
Gesture recognition module with individual detectors and state machine
"""
import math
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from collections import deque
import config
from calibration import CalibrationData
from utils import calculate_distance


class GestureState(Enum):
    """States for the gesture state machine"""
    IDLE = "idle"
    GESTURE_STARTING = "starting"
    GESTURE_CONFIRMED = "confirmed"
    COOLDOWN = "cooldown"


@dataclass
class GestureEvent:
    """Event emitted when a gesture is confirmed"""
    gesture_type: str
    confidence: float
    timestamp: float
    state: GestureState


class LeanDetector:
    """Detects left/right torso lean"""

    def __init__(self):
        self.threshold_angle = config.THRESHOLDS["lean_angle"]

    def detect(self, landmarks: dict, calibration: CalibrationData) -> Optional[str]:
        """
        Calculate torso tilt angle from vertical
        Returns: "lean_left", "lean_right", or None
        """
        # Calculate torso vector (from hip center to shoulder center)
        hip_center_x = (landmarks['left_hip'][0] + landmarks['right_hip'][0]) / 2
        shoulder_center_x = (landmarks['left_shoulder'][0] + landmarks['right_shoulder'][0]) / 2
        hip_center_y = (landmarks['left_hip'][1] + landmarks['right_hip'][1]) / 2
        shoulder_center_y = (landmarks['left_shoulder'][1] + landmarks['right_shoulder'][1]) / 2

        # Calculate angle from vertical (in degrees)
        dx = shoulder_center_x - hip_center_x
        dy = shoulder_center_y - hip_center_y
        angle = math.degrees(math.atan2(dx, dy))

        # Subtract calibrated neutral angle
        relative_angle = angle - calibration.neutral_torso_angle

        if relative_angle < -self.threshold_angle:
            return "lean_left"
        elif relative_angle > self.threshold_angle:
            return "lean_right"
        return None


class HandsRaisedDetector:
    """Detects both hands raised above shoulders"""

    def __init__(self):
        self.threshold_ratio = config.THRESHOLDS["hands_raised_ratio"]
        self.min_visibility = config.THRESHOLDS["min_visibility"]

    def detect(self, landmarks: dict) -> bool:
        """Check if both hands are raised above shoulders"""
        shoulder_avg_y = (landmarks['left_shoulder'][1] + landmarks['right_shoulder'][1]) / 2

        # Calculate torso length for this frame
        hip_center_y = (landmarks['left_hip'][1] + landmarks['right_hip'][1]) / 2
        torso_length = abs(shoulder_avg_y - hip_center_y)

        # Check both wrists
        left_raised = landmarks['left_wrist'][1] < shoulder_avg_y - (self.threshold_ratio * torso_length)
        right_raised = landmarks['right_wrist'][1] < shoulder_avg_y - (self.threshold_ratio * torso_length)

        # Check visibility
        both_visible = (landmarks['left_wrist'][3] > self.min_visibility and
                       landmarks['right_wrist'][3] > self.min_visibility)

        return left_raised and right_raised and both_visible


class SquatDetector:
    """Detects squatting motion (hip lowering)"""

    def __init__(self):
        self.threshold_ratio = config.THRESHOLDS["squat_drop_ratio"]

    def detect(self, landmarks: dict, calibration: CalibrationData) -> bool:
        """Detect hip lowering (squat)"""
        current_hip_y = (landmarks['left_hip'][1] + landmarks['right_hip'][1]) / 2

        # Calculate drop from calibrated neutral position
        hip_drop = current_hip_y - calibration.neutral_hip_height

        # Normalize by torso length
        normalized_drop = hip_drop / calibration.torso_length

        return normalized_drop > self.threshold_ratio


class PunchDetector:
    """Detects forward punch motion based on velocity and depth"""

    def __init__(self):
        self.velocity_threshold = config.THRESHOLDS["punch_velocity"]
        self.depth_threshold = config.THRESHOLDS["punch_depth"]
        self.min_visibility = config.THRESHOLDS["min_visibility"]
        self.prev_landmarks = None
        self.velocity_history = {'left': deque(maxlen=3), 'right': deque(maxlen=3)}

    def detect(self, landmarks: dict, calibration: CalibrationData) -> Optional[str]:
        """
        Detect forward punch based on wrist velocity and depth change
        Returns: "punch_left", "punch_right", or None
        """
        if self.prev_landmarks is None:
            self.prev_landmarks = landmarks
            return None

        dt = landmarks['timestamp'] - self.prev_landmarks['timestamp']
        if dt < 0.001:  # Avoid division by zero
            return None

        # Calculate velocity for each hand
        left_velocity = self._calculate_velocity(
            landmarks['left_wrist'],
            self.prev_landmarks['left_wrist'],
            dt
        )
        right_velocity = self._calculate_velocity(
            landmarks['right_wrist'],
            self.prev_landmarks['right_wrist'],
            dt
        )

        # Update velocity history (for smoothing)
        self.velocity_history['left'].append(left_velocity)
        self.velocity_history['right'].append(right_velocity)

        # Calculate average velocity
        avg_left_vel = sum(self.velocity_history['left']) / len(self.velocity_history['left']) if self.velocity_history['left'] else 0
        avg_right_vel = sum(self.velocity_history['right']) / len(self.velocity_history['right']) if self.velocity_history['right'] else 0

        # Check depth change (forward motion in z-axis - negative is forward)
        left_depth_change = landmarks['left_wrist'][2] - calibration.wrist_neutral_z
        right_depth_change = landmarks['right_wrist'][2] - calibration.wrist_neutral_z

        self.prev_landmarks = landmarks

        # Detect right punch (higher priority for right-handed users)
        if (avg_right_vel > self.velocity_threshold and
            right_depth_change < -self.depth_threshold and
            landmarks['right_wrist'][3] > self.min_visibility):
            return "punch_right"

        # Detect left punch
        if (avg_left_vel > self.velocity_threshold and
            left_depth_change < -self.depth_threshold and
            landmarks['left_wrist'][3] > self.min_visibility):
            return "punch_left"

        return None

    def _calculate_velocity(self, current, previous, dt):
        """Calculate 2D velocity magnitude"""
        dx = current[0] - previous[0]
        dy = current[1] - previous[1]
        return math.sqrt(dx**2 + dy**2) / dt


class CrossedArmsDetector:
    """Detects arms crossed in front of body"""

    def __init__(self):
        self.cross_threshold = config.THRESHOLDS["crossed_arms_offset"]
        self.min_visibility = config.THRESHOLDS["min_visibility"]

    def detect(self, landmarks: dict) -> bool:
        """Detect arms crossed in front of body"""
        # Calculate body center
        body_center_x = (landmarks['left_shoulder'][0] + landmarks['right_shoulder'][0]) / 2

        # Left wrist should be right of body center
        left_crossed = landmarks['left_wrist'][0] > body_center_x + self.cross_threshold

        # Right wrist should be left of body center
        right_crossed = landmarks['right_wrist'][0] < body_center_x - self.cross_threshold

        # Both should be in front of body (y-position between shoulders and hips)
        shoulder_y = (landmarks['left_shoulder'][1] + landmarks['right_shoulder'][1]) / 2
        hip_y = (landmarks['left_hip'][1] + landmarks['right_hip'][1]) / 2

        left_in_front = shoulder_y < landmarks['left_wrist'][1] < hip_y
        right_in_front = shoulder_y < landmarks['right_wrist'][1] < hip_y

        # Check visibility
        both_visible = (landmarks['left_wrist'][3] > self.min_visibility and
                       landmarks['right_wrist'][3] > self.min_visibility)

        return left_crossed and right_crossed and left_in_front and right_in_front and both_visible


class GestureStateMachine:
    """State machine for gesture confirmation and cooldown"""

    def __init__(self):
        self.state = GestureState.IDLE
        self.current_gesture = None
        self.gesture_start_time = 0
        self.last_trigger_time = {}
        self.confirmation_threshold = config.TIMING["confirmation_duration"]
        self.cooldown_duration = config.TIMING["cooldown_duration"]

    def update(self, detected_gesture: Optional[str], confidence: float,
               current_time: float) -> Optional[GestureEvent]:
        """
        Update state machine and return GestureEvent if gesture confirmed
        State transitions:
        IDLE → GESTURE_STARTING: Gesture detected with confidence > threshold
        GESTURE_STARTING → GESTURE_CONFIRMED: Gesture held for confirmation_threshold
        GESTURE_STARTING → IDLE: Gesture lost before confirmation
        GESTURE_CONFIRMED → COOLDOWN: Input sent
        COOLDOWN → IDLE: Cooldown expires
        """

        if self.state == GestureState.IDLE:
            if detected_gesture and confidence > 0.7:
                self.state = GestureState.GESTURE_STARTING
                self.current_gesture = detected_gesture
                self.gesture_start_time = current_time

        elif self.state == GestureState.GESTURE_STARTING:
            if detected_gesture == self.current_gesture:
                if current_time - self.gesture_start_time > self.confirmation_threshold:
                    self.state = GestureState.GESTURE_CONFIRMED
                    return self._create_gesture_event(confidence, current_time)
            else:
                # Gesture lost before confirmation
                self.state = GestureState.IDLE
                self.current_gesture = None

        elif self.state == GestureState.GESTURE_CONFIRMED:
            self.state = GestureState.COOLDOWN
            self.last_trigger_time[self.current_gesture] = current_time

        elif self.state == GestureState.COOLDOWN:
            if current_time - self.last_trigger_time.get(self.current_gesture, 0) > self.cooldown_duration:
                self.state = GestureState.IDLE
                self.current_gesture = None

        return None

    def _create_gesture_event(self, confidence: float, timestamp: float) -> GestureEvent:
        """Create a gesture event"""
        return GestureEvent(
            gesture_type=self.current_gesture,
            confidence=confidence,
            timestamp=timestamp,
            state=self.state
        )


class GestureRecognizer:
    """Main gesture recognition coordinator"""

    def __init__(self, calibration: CalibrationData):
        self.lean_detector = LeanDetector()
        self.hands_raised_detector = HandsRaisedDetector()
        self.squat_detector = SquatDetector()
        self.punch_detector = PunchDetector()
        self.crossed_arms_detector = CrossedArmsDetector()
        self.calibration = calibration
        self.state_machine = GestureStateMachine()

    def recognize(self, landmarks: dict) -> Optional[str]:
        """
        Recognize gesture with priority order to prevent conflicts
        Priority (highest to lowest):
        1. Arms crossed (requires specific hand positioning)
        2. Hands raised (requires both hands)
        3. Punch (requires velocity, more specific)
        4. Squat (full body movement)
        5. Lean (least specific, base movement)

        Returns gesture name or None
        """
        detected_gesture = None
        confidence = 0.0

        # Priority 1: Arms crossed
        if self.crossed_arms_detector.detect(landmarks):
            detected_gesture = "block"
            confidence = 0.9

        # Priority 2: Hands raised
        elif self.hands_raised_detector.detect(landmarks):
            detected_gesture = "jump"
            confidence = 0.9

        # Priority 3: Punch (check both)
        elif detected_gesture is None:
            punch = self.punch_detector.detect(landmarks, self.calibration)
            if punch == "punch_right":
                detected_gesture = "attack_basic"
                confidence = 0.85
            elif punch == "punch_left":
                detected_gesture = "attack_special"
                confidence = 0.85

        # Priority 4: Squat
        if detected_gesture is None and self.squat_detector.detect(landmarks, self.calibration):
            detected_gesture = "crouch"
            confidence = 0.8

        # Priority 5: Lean
        if detected_gesture is None:
            lean = self.lean_detector.detect(landmarks, self.calibration)
            if lean == "lean_left":
                detected_gesture = "move_left"
                confidence = 0.75
            elif lean == "lean_right":
                detected_gesture = "move_right"
                confidence = 0.75

        # Update state machine
        current_time = time.perf_counter()
        gesture_event = self.state_machine.update(detected_gesture, confidence, current_time)

        if gesture_event:
            return gesture_event.gesture_type

        return None
