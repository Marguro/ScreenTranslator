from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer
from src.utils import StyleManager

class StatusIndicator(QLabel):
    """Status indicator widget"""

    def __init__(self, initial_text="Ready", color_key='success'):
        super().__init__(initial_text)
        self.update_status(initial_text, color_key)

    def update_status(self, text, color_key='success'):
        """Update status with color"""
        color = StyleManager.COLORS[color_key]
        rgb = StyleManager._hex_to_rgb(color)

        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font: 11px 'Segoe UI';
                background: rgba({rgb}, 0.1);
                border: 1px solid rgba({rgb}, 0.3);
                border-radius: 8px;
                padding: 4px 8px;
                max-width: 80px;
                max-height: 20px;
            }}
        """)


class CopyIndicator(QLabel):
    """Copy indicator widget"""

    def __init__(self):
        super().__init__("📋 Copied!")
        color = StyleManager.COLORS['primary']
        rgb = StyleManager._hex_to_rgb(color)

        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font: 11px 'Segoe UI';
                background: rgba({rgb}, 0.1);
                border: 1px solid rgba({rgb}, 0.3);
                border-radius: 8px;
                padding: 4px 8px;
                max-width: 90px;
                max-height: 20px;
            }}
        """)
        self.hide()

    def show_briefly(self, duration=2000):
        """Show indicator for a brief period"""
        self.show()
        QTimer.singleShot(duration, self.hide)