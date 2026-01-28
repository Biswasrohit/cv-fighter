"""
Mock pose data for testing gesture recognition
"""


def create_mock_landmarks(overrides=None):
    """
    Create mock landmarks with default T-pose values
    Can override specific landmarks for testing
    """
    defaults = {
        'left_shoulder': (0.3, 0.3, 0.0, 1.0),
        'right_shoulder': (0.7, 0.3, 0.0, 1.0),
        'left_elbow': (0.2, 0.5, 0.0, 1.0),
        'right_elbow': (0.8, 0.5, 0.0, 1.0),
        'left_wrist': (0.1, 0.5, 0.0, 1.0),
        'right_wrist': (0.9, 0.5, 0.0, 1.0),
        'left_hip': (0.35, 0.7, 0.0, 1.0),
        'right_hip': (0.65, 0.7, 0.0, 1.0),
        'left_knee': (0.35, 0.85, 0.0, 1.0),
        'right_knee': (0.65, 0.85, 0.0, 1.0),
        'left_ankle': (0.35, 1.0, 0.0, 1.0),
        'right_ankle': (0.65, 1.0, 0.0, 1.0),
        'timestamp': 0.0
    }

    if overrides:
        defaults.update(overrides)

    return defaults


# Predefined test poses
NEUTRAL_POSE = create_mock_landmarks()

LEAN_LEFT_POSE = create_mock_landmarks({
    'left_shoulder': (0.25, 0.3, 0.0, 1.0),
    'right_shoulder': (0.65, 0.3, 0.0, 1.0),
    'left_hip': (0.30, 0.7, 0.0, 1.0),
    'right_hip': (0.60, 0.7, 0.0, 1.0),
})

LEAN_RIGHT_POSE = create_mock_landmarks({
    'left_shoulder': (0.35, 0.3, 0.0, 1.0),
    'right_shoulder': (0.75, 0.3, 0.0, 1.0),
    'left_hip': (0.40, 0.7, 0.0, 1.0),
    'right_hip': (0.70, 0.7, 0.0, 1.0),
})

HANDS_RAISED_POSE = create_mock_landmarks({
    'left_wrist': (0.2, 0.15, 0.0, 1.0),
    'right_wrist': (0.8, 0.15, 0.0, 1.0),
})

SQUAT_POSE = create_mock_landmarks({
    'left_hip': (0.35, 0.8, 0.0, 1.0),
    'right_hip': (0.65, 0.8, 0.0, 1.0),
    'left_knee': (0.35, 0.9, 0.0, 1.0),
    'right_knee': (0.65, 0.9, 0.0, 1.0),
})

# Punch sequence (3 frames showing forward motion)
PUNCH_RIGHT_POSE_SEQUENCE = [
    create_mock_landmarks({'right_wrist': (0.9, 0.5, 0.0, 1.0), 'timestamp': 0.0}),
    create_mock_landmarks({'right_wrist': (0.95, 0.5, -0.1, 1.0), 'timestamp': 0.033}),
    create_mock_landmarks({'right_wrist': (1.0, 0.5, -0.2, 1.0), 'timestamp': 0.066}),
]

PUNCH_LEFT_POSE_SEQUENCE = [
    create_mock_landmarks({'left_wrist': (0.1, 0.5, 0.0, 1.0), 'timestamp': 0.0}),
    create_mock_landmarks({'left_wrist': (0.05, 0.5, -0.1, 1.0), 'timestamp': 0.033}),
    create_mock_landmarks({'left_wrist': (0.0, 0.5, -0.2, 1.0), 'timestamp': 0.066}),
]

CROSSED_ARMS_POSE = create_mock_landmarks({
    'left_wrist': (0.6, 0.5, 0.0, 1.0),
    'right_wrist': (0.4, 0.5, 0.0, 1.0),
})
