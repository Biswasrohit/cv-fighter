"""
CV Fighter - Main application entry point
Computer vision controlled fighting game input system
"""
import cv2
import threading
import time
import sys
from capture import WebcamCapture, FrameData
from pose_detector import PoseDetector
from gesture_recognizer import GestureRecognizer, GestureResult
from input_simulator import InputSimulator, InputCommand
from calibration import CalibrationSystem
from utils import SharedState, check_permissions
import config


class CVFighterApp:
    """Main application class"""

    def __init__(self):
        self.shared_state = SharedState()
        self.capture = WebcamCapture(self.shared_state)
        self.pose_detector = PoseDetector()
        self.calibration_system = CalibrationSystem()
        self.gesture_recognizer = None  # Created after calibration
        self.input_simulator = InputSimulator(self.shared_state)

        self.threads = []
        self.is_calibrated = False
        self.active_held_keys = {}  # gesture -> key mapping for currently held keys

    def initialize(self) -> bool:
        """Initialize all components"""
        print("\n" + "="*60)
        print(" "*15 + "CV FIGHTER")
        print(" "*10 + "Body-Controlled Gaming")
        print("="*60)
        print()

        # Check permissions
        if not check_permissions():
            return False

        # Initialize camera
        if not self.capture.initialize_camera():
            print("Error: Failed to initialize camera")
            return False

        print("Camera initialized successfully")
        print()
        return True

    def run(self):
        """Main application loop"""
        # Set running flag
        self.shared_state.is_running.set()

        # Start capture thread
        capture_thread = threading.Thread(target=self.capture.capture_loop, daemon=True)
        capture_thread.start()
        self.threads.append(capture_thread)

        # Start input simulator thread
        input_thread = threading.Thread(target=self.input_simulator.process_loop, daemon=True)
        input_thread.start()
        self.threads.append(input_thread)

        # Main processing loop
        cv2.namedWindow("CV Fighter")

        print("Controls:")
        print("  'q' - Quit")
        print("  SPACE - Pause/Resume")
        print("  'd' - Toggle debug mode")
        print("  'r' - Recalibrate")
        print()

        try:
            while self.shared_state.is_running.is_set():
                # Get frame from queue
                try:
                    frame_data = self.shared_state.frame_queue.get(timeout=0.1)
                except:
                    continue

                # Process frame
                display_frame = self._process_frame(frame_data)

                # Show frame
                cv2.imshow("CV Fighter", display_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    if self.shared_state.is_paused.is_set():
                        self.shared_state.is_paused.clear()
                        print("Resumed")
                    else:
                        self.shared_state.is_paused.set()
                        print("Paused")
                elif key == ord('d'):
                    if self.shared_state.debug_mode.is_set():
                        self.shared_state.debug_mode.clear()
                        print("Debug mode OFF")
                    else:
                        self.shared_state.debug_mode.set()
                        print("Debug mode ON")
                elif key == ord('r'):
                    self.is_calibrated = False
                    self.calibration_system = CalibrationSystem()
                    print("Restarting calibration...")

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

    def _process_frame(self, frame_data: FrameData):
        """Process single frame"""
        start_time = time.perf_counter()

        # Detect pose
        landmarks, results = self.pose_detector.detect(frame_data.frame)

        display_frame = frame_data.mirrored.copy()

        if landmarks is None:
            # No pose detected
            self._draw_status(display_frame, "No pose detected", (0, 0, 255))
            return display_frame

        # Draw landmarks
        if results:
            self.pose_detector.draw_landmarks(display_frame, results)

        # Calibration phase
        if not self.is_calibrated:
            if self.calibration_system.start_time is None:
                self.calibration_system.start_calibration()

            is_complete, progress = self.calibration_system.update(landmarks)

            # Draw calibration progress
            self._draw_calibration_progress(display_frame, progress)

            if is_complete:
                self.is_calibrated = True
                self.gesture_recognizer = GestureRecognizer(
                    self.calibration_system.calibration_data
                )

            return display_frame

        # Gesture recognition
        result = self.gesture_recognizer.recognize(landmarks)

        # Handle hold gestures (movement keys held while gesture active)
        self._handle_hold_gestures(result.raw_gesture)

        # Handle tap gestures (single press on confirmation)
        if result.confirmed_gesture and result.confirmed_gesture in config.TAP_GESTURES:
            key = config.GESTURE_KEY_MAPPING.get(result.confirmed_gesture)
            if key:
                # Send press
                self._send_input(key, "press", result.confirmed_gesture)
                # Send release shortly after for tap gestures
                self._send_input(key, "release", result.confirmed_gesture)

        # Update shared state for display
        display_gesture = result.raw_gesture or result.confirmed_gesture
        if display_gesture:
            with self.shared_state.gesture_lock:
                self.shared_state.current_gesture = display_gesture

        # Draw overlay
        self._draw_overlay(display_frame, display_gesture)

        # Calculate latency
        latency = (time.perf_counter() - start_time) * 1000
        with self.shared_state.metrics_lock:
            self.shared_state.latency_metrics["total"] = latency

        return display_frame

    def _draw_overlay(self, frame, gesture):
        """Draw UI overlay"""
        # Current gesture
        if gesture:
            gesture_text = gesture.replace('_', ' ').title()
            key = config.GESTURE_KEY_MAPPING.get(gesture, '?')
            text = f"{gesture_text} -> {key.upper()}"
            cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                       1.0, (0, 255, 0), 2)

        # FPS
        if config.DEBUG["show_fps"]:
            fps_text = f"FPS: {self.capture.current_fps:.1f}"
            cv2.putText(frame, fps_text, (10, 75), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, (255, 255, 255), 1)

        # Latency
        if config.DEBUG["show_latency"]:
            with self.shared_state.metrics_lock:
                latency = self.shared_state.latency_metrics.get("total", 0)
            latency_text = f"Latency: {latency:.1f}ms"
            color = (0, 255, 0) if latency < 100 else (0, 255, 255) if latency < 150 else (0, 0, 255)
            cv2.putText(frame, latency_text, (10, 105), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 1)

        # Debug mode indicator
        if self.shared_state.debug_mode.is_set():
            cv2.putText(frame, "DEBUG MODE", (frame.shape[1] - 200, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Paused indicator
        if self.shared_state.is_paused.is_set():
            cv2.putText(frame, "PAUSED", (frame.shape[1] // 2 - 80, frame.shape[0] // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 3)

    def _draw_calibration_progress(self, frame, progress):
        """Draw calibration progress bar"""
        text = "Hold T-Pose for Calibration"
        cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                   1.0, (0, 255, 255), 2)

        # Progress bar
        bar_width = 400
        bar_height = 30
        bar_x = (frame.shape[1] - bar_width) // 2
        bar_y = 80

        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     (255, 255, 255), 2)

        # Fill
        fill_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                     (0, 255, 0), -1)

        # Percentage text
        percent_text = f"{int(progress * 100)}%"
        text_size = cv2.getTextSize(percent_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = bar_x + (bar_width - text_size[0]) // 2
        text_y = bar_y + (bar_height + text_size[1]) // 2
        cv2.putText(frame, percent_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    def _draw_status(self, frame, text, color):
        """Draw status message"""
        cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                   1.0, color, 2)

    def _handle_hold_gestures(self, raw_gesture: str):
        """Handle hold-type gestures (press while active, release when done)"""
        # Determine which hold gesture is currently active (if any)
        current_hold = None
        if raw_gesture and raw_gesture in config.HOLD_GESTURES:
            current_hold = raw_gesture

        # Release keys for gestures that are no longer active
        gestures_to_release = []
        for gesture, key in self.active_held_keys.items():
            if gesture != current_hold:
                self._send_input(key, "release", gesture)
                gestures_to_release.append(gesture)

        for gesture in gestures_to_release:
            del self.active_held_keys[gesture]

        # Press key for new hold gesture
        if current_hold and current_hold not in self.active_held_keys:
            key = config.GESTURE_KEY_MAPPING.get(current_hold)
            if key:
                self._send_input(key, "press", current_hold)
                self.active_held_keys[current_hold] = key

    def _send_input(self, key: str, action: str, gesture_source: str):
        """Send input command to the input queue"""
        command = InputCommand(
            key=key,
            action=action,
            timestamp=time.perf_counter(),
            gesture_source=gesture_source
        )
        try:
            self.shared_state.input_queue.put_nowait(command)
        except:
            pass  # Queue full, skip this input

    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")

        # Signal threads to stop
        self.shared_state.is_running.clear()

        # Release all held gesture keys
        for gesture, key in self.active_held_keys.items():
            self._send_input(key, "release", gesture)
        self.active_held_keys.clear()

        # Release all keys in input simulator
        self.input_simulator.release_all_keys()

        # Wait for threads
        for thread in self.threads:
            thread.join(timeout=1.0)

        # Release camera
        self.capture.release()

        # Close pose detector
        self.pose_detector.close()

        # Close windows
        cv2.destroyAllWindows()

        print("Shutdown complete")


def main():
    """Entry point"""
    app = CVFighterApp()

    if not app.initialize():
        print("\nInitialization failed. Exiting.")
        sys.exit(1)

    app.run()


if __name__ == "__main__":
    main()
