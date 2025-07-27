import time
import keyboard
from PyQt6.QtCore import QTimer
from src.config import Config

class KeyboardManager:
    """Handles keyboard events"""

    def __init__(self, callback):
        self.callback = callback
        self.last_alt_press_time = 0
        keyboard.on_press(self._on_key_press)

    def _on_key_press(self, event):
        """Handle key press events"""
        if event.event_type == keyboard.KEY_DOWN and event.name == 'alt':
            current_time = time.time()
            time_diff = current_time - self.last_alt_press_time

            if 0.1 < time_diff < Config.ALT_DOUBLE_PRESS_THRESHOLD:
                print("\n[INFO] Double Alt detected! Starting screen selection...")
                QTimer.singleShot(100, self.callback)

            self.last_alt_press_time = current_time

    def cleanup(self):
        """Clean up keyboard hooks"""
        try:
            keyboard.unhook_all()
        except Exception as e:
            print(f"Could not unhook keyboard: {e}")