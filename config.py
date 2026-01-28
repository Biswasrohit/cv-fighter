"""
Configuration for CV Fighter
All thresholds and mappings are defined here for easy tuning
"""

# Gesture to keyboard mappings
GESTURE_KEY_MAPPING = {
    "move_left": "a",
    "move_right": "d",
    "jump": "w",
    "crouch": "s",
    "attack_basic": "j",
    "attack_special": "k",
    "block": "l"
}

# Gesture detection thresholds
THRESHOLDS = {
    "lean_angle": 15.0,              # degrees from vertical
    "hands_raised_ratio": 0.2,       # ratio of torso length above shoulders
    "squat_drop_ratio": 0.25,        # ratio of torso length hip drops
    "punch_velocity": 1.5,           # normalized units per second
    "punch_depth": 0.15,             # z-coordinate change threshold
    "crossed_arms_offset": 0.1,      # ratio for wrist crossing detection
    "min_visibility": 0.5,           # minimum landmark visibility confidence
}

# State machine timing
TIMING = {
    "confirmation_duration": 0.1,    # seconds to confirm gesture
    "cooldown_duration": 0.2,        # seconds between same gesture
    "calibration_duration": 3.0,     # seconds for T-pose calibration
}

# Video capture settings
CAPTURE = {
    "resolution": (640, 480),        # (width, height) - prioritize latency
    "fps_target": 30,
    "frame_queue_size": 2,           # Drop old frames if processing is slow
    "mirror_display": True,
}

# MediaPipe configuration
MEDIAPIPE = {
    "model_complexity": 1,           # 0=Lite, 1=Full, 2=Heavy (balance speed/accuracy)
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5,
    "smooth_landmarks": True,
}

# Window detection
WINDOW_DETECTION = {
    "browser_names": ["Google Chrome", "Firefox", "Safari", "Microsoft Edge"],
    "game_title_keywords": ["Super Smash Flash", "McLeodGaming", "SSF2"],
    "focus_check_interval": 1.0,     # seconds between window focus checks
}

# Debug settings
DEBUG = {
    "show_fps": True,
    "show_latency": True,
    "show_landmarks": False,         # Toggle with 'd' key
    "show_gesture_name": True,
    "overlay_color": (0, 255, 0),    # BGR green
    "text_color": (255, 255, 255),   # BGR white
}

# Performance targets
PERFORMANCE = {
    "target_latency_ms": 150,        # End-to-end latency target
    "max_processing_time_ms": 33,    # Max time per frame at 30fps
}
