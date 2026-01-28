"""
Unit tests for gesture state machine
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from gesture_recognizer import GestureStateMachine, GestureState


class TestGestureStateMachine(unittest.TestCase):
    def setUp(self):
        self.fsm = GestureStateMachine()

    def test_idle_to_starting(self):
        """Test transition from IDLE to GESTURE_STARTING"""
        self.assertEqual(self.fsm.state, GestureState.IDLE)

        result = self.fsm.update("jump", confidence=0.8, current_time=0.0)

        self.assertEqual(self.fsm.state, GestureState.GESTURE_STARTING)
        self.assertIsNone(result)

    def test_starting_to_confirmed(self):
        """Test gesture confirmation after threshold"""
        self.fsm.update("jump", confidence=0.8, current_time=0.0)
        self.fsm.update("jump", confidence=0.8, current_time=0.05)
        result = self.fsm.update("jump", confidence=0.8, current_time=0.15)

        self.assertEqual(self.fsm.state, GestureState.GESTURE_CONFIRMED)
        self.assertIsNotNone(result)
        self.assertEqual(result.gesture_type, "jump")

    def test_starting_to_idle_on_gesture_lost(self):
        """Test return to IDLE if gesture is lost before confirmation"""
        self.fsm.update("jump", confidence=0.8, current_time=0.0)
        self.assertEqual(self.fsm.state, GestureState.GESTURE_STARTING)

        # Gesture lost
        result = self.fsm.update(None, confidence=0.0, current_time=0.05)

        self.assertEqual(self.fsm.state, GestureState.IDLE)
        self.assertIsNone(result)

    def test_cooldown_prevents_repeat(self):
        """Test cooldown prevents immediate repeat"""
        # Trigger gesture
        self.fsm.update("jump", confidence=0.8, current_time=0.0)
        self.fsm.update("jump", confidence=0.8, current_time=0.15)

        # Should be in cooldown
        self.assertEqual(self.fsm.state, GestureState.COOLDOWN)

        # Try to trigger again immediately (should not work)
        self.fsm.update("jump", confidence=0.8, current_time=0.20)
        result = self.fsm.update("jump", confidence=0.8, current_time=0.25)
        self.assertIsNone(result)

    def test_cooldown_expires(self):
        """Test cooldown expiration allows new gesture"""
        # Trigger and complete gesture
        self.fsm.update("jump", confidence=0.8, current_time=0.0)
        self.fsm.update("jump", confidence=0.8, current_time=0.15)

        # Wait for cooldown to expire
        self.fsm.update(None, confidence=0.0, current_time=0.50)

        self.assertEqual(self.fsm.state, GestureState.IDLE)

    def test_low_confidence_not_triggered(self):
        """Test that low confidence gestures don't trigger"""
        result = self.fsm.update("jump", confidence=0.5, current_time=0.0)

        self.assertEqual(self.fsm.state, GestureState.IDLE)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
