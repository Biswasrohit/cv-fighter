# CV Fighter

A computer vision-based fighting game controller that allows you to play browser games like Super Smash Flash 2 using body movements instead of a keyboard.

## Features

- Real-time pose detection using MediaPipe
- 6 gesture types mapped to game controls
- Low-latency input simulation (<150ms target)
- Automatic calibration system
- Debug mode with FPS and latency metrics
- macOS window detection for seamless input routing

## Gesture Mappings

| Gesture | Key | Description |
|---------|-----|-------------|
| Lean Left | A | Move character left |
| Lean Right | D | Move character right |
| Hands Raised | W | Jump |
| Squat | S | Crouch/Drop |
| Right Punch | J | Basic Attack |
| Left Punch | K | Special Attack |
| Arms Crossed | L | Block/Shield |

## Requirements

- Python 3.10+
- macOS (for window detection features)
- Webcam
- Good lighting conditions

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## macOS Permissions

Before running the application, you need to grant the following permissions:

### 1. Camera Access
- Go to **System Preferences → Security & Privacy → Camera**
- Enable access for Terminal (or your Python environment)

### 2. Accessibility
- Go to **System Preferences → Security & Privacy → Accessibility**
- Enable access for Terminal (or your Python environment)
- Required for keyboard input simulation

### 3. Screen Recording (Optional)
- Go to **System Preferences → Security & Privacy → Screen Recording**
- Enable access for Terminal
- Required for automatic game window detection

**Note:** You may need to restart Terminal after granting permissions.

## Usage

1. Open Super Smash Flash 2 (or another browser game) in your browser

2. Run the application:
```bash
python main.py
```

3. Stand back from your webcam so your full body is visible

4. Hold a **T-pose** for 3 seconds to calibrate:
   - Feet shoulder-width apart
   - Arms extended horizontally to the sides
   - Stand straight, facing the camera

5. Once calibrated, start playing! The application will detect your gestures and send keyboard inputs to the game.

### Controls

- **Q** - Quit the application
- **P** - Pause/Resume gesture detection
- **D** - Toggle debug mode (show landmark coordinates)
- **R** - Restart calibration

## Configuration

Edit [config.py](config.py) to customize:

- **Gesture thresholds** - Adjust sensitivity for each gesture
- **Timing** - Confirmation and cooldown durations
- **Key mappings** - Change which keys are pressed for each gesture
- **Video settings** - Resolution, FPS, etc.
- **Debug options** - Toggle FPS/latency display

### Example: Adjusting Lean Sensitivity

```python
# In config.py
THRESHOLDS = {
    "lean_angle": 20.0,  # Increase from 15.0 for less sensitive detection
    # ...
}
```

## Testing

Run unit tests:

```bash
# Test gesture recognition
python -m pytest tests/test_gesture_recognition.py

# Test state machine
python -m pytest tests/test_state_machine.py

# Run all tests
python -m pytest tests/
```

Or using unittest:

```bash
python -m unittest discover tests
```

## Architecture

The application uses a **producer-consumer** architecture with 3 threads:

1. **Capture Thread** - Continuously captures webcam frames
2. **Processing Thread** - Detects poses and recognizes gestures
3. **Main Thread** - Manages UI and event loop

```
Webcam → Capture → Frame Queue → Processing → Pose Detection →
Gesture Recognition → Input Queue → Input Simulator → Browser
                              ↓
                      Preview Window (with overlays)
```

## Troubleshooting

### Camera not working
- Check that your webcam is connected
- Grant camera permissions in System Preferences
- Try restarting the application

### No pose detected
- Ensure your full body is visible in the frame
- Check lighting conditions (brighter is better)
- Move farther from the camera
- Stand against a simple background

### Gestures not triggering
- Complete calibration in a proper T-pose
- Exaggerate your movements
- Adjust thresholds in config.py
- Enable debug mode (D key) to see detection status

### Inputs not reaching the game
- Keep the browser window focused
- The application will warn if it can't find the game window
- Try clicking on the browser window manually

### High latency
- Lower resolution in config.py (already at 640x480)
- Close other applications
- Check FPS counter - should be ~30fps
- Reduce MediaPipe model complexity in config.py

## Performance Targets

- **FPS**: 30+ (actual varies by hardware)
- **End-to-end latency**: <150ms
- **Pose detection**: ~20-25ms per frame
- **Gesture recognition**: ~2ms per frame

## Limitations

- macOS only (window detection uses PyObjC)
- Single player (detects one person)
- Requires good lighting and full body visibility
- Some gestures may conflict (handled by priority system)

## Project Structure

```
cv-fighter/
├── main.py              # Entry point and orchestration
├── capture.py           # Webcam capture thread
├── pose_detector.py     # MediaPipe pose detection wrapper
├── gesture_recognizer.py # Gesture detectors and state machine
├── input_simulator.py   # Window detection and keyboard simulation
├── calibration.py       # T-pose calibration system
├── config.py            # Configuration and thresholds
├── utils.py             # Shared state and helper functions
├── requirements.txt     # Python dependencies
├── tests/
│   ├── mock_data.py            # Mock pose data for testing
│   ├── test_gesture_recognition.py
│   └── test_state_machine.py
└── README.md
```

## Future Enhancements

- Cross-platform support (Windows, Linux)
- Two-player split-screen mode
- Custom gesture training UI
- Gesture recording/playback for testing
- Sensitivity adjustment UI
- Profile persistence (save calibration)

## Technical Details

### Gesture Detection Algorithms

**Lean Detection**: Calculates torso tilt angle by measuring the horizontal offset between shoulder center and hip center.

**Hands Raised**: Checks if both wrists are positioned above shoulders by at least 20% of torso length.

**Squat Detection**: Measures hip height drop compared to calibrated neutral position (>25% of torso length).

**Punch Detection**: Combines wrist velocity (>1.5 units/sec) with forward depth change in z-axis (<-0.15).

**Crossed Arms**: Detects when left wrist crosses right of body center and right wrist crosses left.

### State Machine

Gestures go through 4 states:
1. **IDLE** - No gesture detected
2. **GESTURE_STARTING** - Gesture detected, awaiting confirmation
3. **GESTURE_CONFIRMED** - Gesture confirmed (>100ms hold), input sent
4. **COOLDOWN** - 200ms cooldown to prevent spam

## Credits

Built with:
- [MediaPipe](https://google.github.io/mediapipe/) - Pose detection
- [OpenCV](https://opencv.org/) - Video capture and processing
- [pynput](https://pynput.readthedocs.io/) - Keyboard simulation

## License

MIT License - feel free to use and modify for your own projects!

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest new gestures
- Improve detection algorithms
- Add cross-platform support

---

**Have fun playing games with your body! 🎮**
