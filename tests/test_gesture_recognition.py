"""
Unit tests for gesture recognition
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from gesture_recognizer import (
    LeanDetector, HandsRaisedDetector, SquatDetector,
    PunchDetector, CrossedArmsDetector
)
from calibration import CalibrationData
from tests.mock_data import *


class TestLeanDetector(unittest.TestCase):
    def setUp(self):
        self.detector = LeanDetector()
        self.calibration = CalibrationData(
            neutral_torso_angle=0.0,
            shoulder_width=0.4,
            torso_length=0.4,
            is_calibrated=True
        )

    def test_neutral_pose(self):
        """Test that neutral T-pose returns no lean"""
        pose = NEUTRAL_POSE
        result = self.detector.detect(pose, self.calibration)
        self.assertIsNone(result)

    def test_lean_left(self):
        """Test left lean detection"""
        result = self.detector.detect(LEAN_LEFT_POSE, self.calibration)
        self.assertEqual(result, "lean_left")

    def test_lean_right(self):
        """Test right lean detection"""
        result = self.detector.detect(LEAN_RIGHT_POSE, self.calibration)
        self.assertEqual(result, "lean_right")


class TestHandsRaisedDetector(unittest.TestCase):
    def setUp(self):
        self.detector = HandsRaisedDetector()

    def test_hands_raised(self):
        """Test hands raised detection"""
        result = self.detector.detect(HANDS_RAISED_POSE)
        self.assertTrue(result)

    def test_hands_not_raised(self):
        """Test normal pose doesn't trigger"""
        pose = NEUTRAL_POSE
        result = self.detector.detect(pose)
        self.assertFalse(result)


class TestSquatDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SquatDetector()
        self.calibration = CalibrationData(
            neutral_hip_height=0.7,
            torso_length=0.4,
            is_calibrated=True
        )

    def test_squat_detected(self):
        """Test squat detection"""
        result = self.detector.detect(SQUAT_POSE, self.calibration)
        self.assertTrue(result)

    def test_standing_not_squat(self):
        """Test standing pose doesn't trigger squat"""
        pose = NEUTRAL_POSE
        result = self.detector.detect(pose, self.calibration)
        self.assertFalse(result)


class TestPunchDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PunchDetector()
        self.calibration = CalibrationData(
            wrist_neutral_z=0.0,
            is_calibrated=True
        )

    def test_punch_right_sequence(self):
        """Test right punch detection with motion sequence"""
        sequence = PUNCH_RIGHT_POSE_SEQUENCE

        # First frame - no detection (no previous frame)
        result = self.detector.detect(sequence[0], self.calibration)
        self.assertIsNone(result)

        # Second and third frames - should detect punch
        for frame in sequence[1:]:
            result = self.detector.detect(frame, self.calibration)
            if result:
                self.assertEqual(result, "punch_right")
                break

    def test_punch_left_sequence(self):
        """Test left punch detection with motion sequence"""
        sequence = PUNCH_LEFT_POSE_SEQUENCE

        result = self.detector.detect(sequence[0], self.calibration)
        self.assertIsNone(result)

        for frame in sequence[1:]:
            result = self.detector.detect(frame, self.calibration)
            if result:
                self.assertEqual(result, "punch_left")
                break


class TestCrossedArmsDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CrossedArmsDetector()

    def test_crossed_arms(self):
        """Test crossed arms detection"""
        result = self.detector.detect(CROSSED_ARMS_POSE)
        self.assertTrue(result)

    def test_normal_pose_not_crossed(self):
        """Test normal pose doesn't trigger crossed arms"""
        pose = NEUTRAL_POSE
        result = self.detector.detect(pose)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
