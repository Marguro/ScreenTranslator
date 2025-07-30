import time
from PyQt6.QtCore import QTimer, QObject, QEvent, Qt
from src.config import Config

class KeyboardManager(QObject):
    """Handles keyboard events using PyQt event filter"""

    def __init__(self, callback, target_widget):
        super().__init__()
        self.callback = callback
        self.last_alt_press_time = 0
        self.target_widget = target_widget
        self.target_widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Alt:
            current_time = time.time()
            time_diff = current_time - self.last_alt_press_time
            if 0.1 < time_diff < Config.ALT_DOUBLE_PRESS_THRESHOLD:
                print("\n[INFO] Double Alt detected! Starting screen selection...")
                QTimer.singleShot(100, self.callback)
            self.last_alt_press_time = current_time
        return super().eventFilter(obj, event)

    def cleanup(self):
        self.target_widget.removeEventFilter(self)
