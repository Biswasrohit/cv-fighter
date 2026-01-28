"""
Utility functions and shared state management for CV Fighter
"""
import threading
import queue
import cv2
import sys
import platform
import math


class SharedState:
    """Thread-safe shared state for communication between threads"""
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=2)
        self.input_queue = queue.Queue(maxsize=10)
        self.is_running = threading.Event()
        self.is_paused = threading.Event()
        self.debug_mode = threading.Event()
        self.current_gesture = None
        self.gesture_lock = threading.Lock()
        self.latency_metrics = {}
        self.metrics_lock = threading.Lock()


def check_permissions() -> bool:
    """Check required system permissions"""
    print("Checking permissions...")

    # Check camera access
    cap = cv2.VideoCapture(0)
    camera_ok = cap.isOpened()
    cap.release()

    if not camera_ok:
        print("\nERROR: Camera access denied")
        if platform.system() == "Darwin":  # macOS
            print("Please grant camera permissions:")
            print("  System Preferences → Security & Privacy → Camera")
            print("  Enable access for Terminal/Python\n")
        return False

    print("  ✓ Camera: OK")

    # Check accessibility (for pynput) on macOS
    if platform.system() == "Darwin":
        try:
            from pynput.keyboard import Controller
            Controller()
            print("  ✓ Accessibility: OK")
        except Exception as e:
            print("\nERROR: Accessibility permissions required")
            print("Please grant permissions:")
            print("  System Preferences → Security & Privacy → Accessibility")
            print("  Enable access for Terminal/Python")
            print("\nYou may need to restart the application after granting permissions.\n")
            return False

    print()
    return True


def calculate_angle(p1, p2, p3):
    """
    Calculate angle between three points
    p2 is the vertex of the angle
    Returns angle in degrees
    """
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)

    if mag1 == 0 or mag2 == 0:
        return 0

    cos_angle = dot / (mag1 * mag2)
    cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]

    return math.degrees(math.acos(cos_angle))


def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
