"""
Input simulation module with window detection and keyboard control
"""
from pynput.keyboard import Controller
import time
import queue
from dataclasses import dataclass
from typing import Optional
import config

# Window detection imports (macOS)
try:
    import Quartz
    from AppKit import NSWorkspace, NSRunningApplication, NSApplicationActivateIgnoringOtherApps
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False
    print("Warning: macOS window detection libraries not available")


@dataclass
class InputCommand:
    """Command to press or release a key"""
    key: str
    action: str  # "press" or "release"
    timestamp: float
    gesture_source: str


class WindowDetector:
    """Detects and focuses the browser window running the game"""

    def __init__(self):
        self.browser_names = config.WINDOW_DETECTION["browser_names"]
        self.game_keywords = config.WINDOW_DETECTION["game_title_keywords"]
        self.cached_window = None
        self.cache_time = 0
        self.cache_duration = 5.0  # Cache window info for 5 seconds

    def find_game_window(self) -> Optional[dict]:
        """Find browser window running the game"""
        if not MACOS_AVAILABLE:
            return None

        # Use cached result if recent
        if self.cached_window and (time.time() - self.cache_time) < self.cache_duration:
            return self.cached_window

        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly |
                Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )

            # First pass: look for game title
            for window in window_list:
                window_title = window.get('kCGWindowName', '')
                owner_name = window.get('kCGWindowOwnerName', '')

                if owner_name not in self.browser_names:
                    continue

                if any(keyword.lower() in window_title.lower() for keyword in self.game_keywords):
                    window_info = {
                        'window_id': window['kCGWindowNumber'],
                        'process_id': window['kCGWindowOwnerPID'],
                        'app_name': owner_name,
                        'title': window_title
                    }
                    self.cached_window = window_info
                    self.cache_time = time.time()
                    print(f"Found game window: {owner_name} - {window_title}")
                    return window_info

            # Fallback: frontmost browser
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()

            if frontmost_app.localizedName() in self.browser_names:
                window_info = {
                    'process_id': frontmost_app.processIdentifier(),
                    'app_name': frontmost_app.localizedName(),
                    'title': 'Frontmost Browser (fallback)'
                }
                print(f"Using frontmost browser: {window_info['app_name']}")
                return window_info

        except Exception as e:
            print(f"Error detecting window: {e}")

        return None

    def focus_window(self, window_info: dict):
        """Bring window to front"""
        if not MACOS_AVAILABLE or not window_info:
            return

        try:
            pid = window_info['process_id']
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
            if app:
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        except Exception as e:
            print(f"Error focusing window: {e}")


class InputSimulator:
    """Simulates keyboard inputs and manages game window focus"""

    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.keyboard = Controller()
        self.window_detector = WindowDetector()
        self.last_focus_check = 0
        self.focus_check_interval = config.WINDOW_DETECTION["focus_check_interval"]
        self.active_keys = set()  # Track pressed keys

    def process_loop(self):
        """Main input processing loop - runs in separate thread"""
        while self.shared_state.is_running.is_set():
            try:
                command = self.shared_state.input_queue.get(timeout=0.1)
                self._send_input(command)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in input processing: {e}")

    def _send_input(self, command: InputCommand):
        """Send keyboard input"""
        # Periodically check/focus game window
        current_time = time.time()
        if current_time - self.last_focus_check > self.focus_check_interval:
            self._ensure_window_focused()
            self.last_focus_check = current_time

        # Send key press/release
        try:
            if command.action == "press":
                if command.key not in self.active_keys:
                    self.keyboard.press(command.key)
                    self.active_keys.add(command.key)
            elif command.action == "release":
                if command.key in self.active_keys:
                    self.keyboard.release(command.key)
                    self.active_keys.discard(command.key)
        except Exception as e:
            print(f"Error sending input: {e}")

    def _ensure_window_focused(self):
        """Ensure game window is focused"""
        window_info = self.window_detector.find_game_window()
        if window_info:
            # Optionally focus window (can be disruptive during gameplay)
            # Uncomment the line below to auto-focus the game window
            # self.window_detector.focus_window(window_info)
            pass
        else:
            if not hasattr(self, '_warning_shown'):
                print("Warning: Game window not found. Please keep the browser focused.")
                print("Looking for browsers: " + ", ".join(self.window_detector.browser_names))
                self._warning_shown = True

    def release_all_keys(self):
        """Release all currently pressed keys"""
        for key in list(self.active_keys):
            try:
                self.keyboard.release(key)
            except:
                pass
        self.active_keys.clear()
