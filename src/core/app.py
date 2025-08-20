import sys
import os
import ollama
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QPalette, QColor, QIcon

from src.config import Config
from src.ui.control_window import ControlWindow

class ScreenTranslatorApp:
    """Main application class"""

    def __init__(self):
        # Note: In PyQt6 (Qt6), high DPI scaling is enabled by default
        # The attributes AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps from Qt5
        # have been removed in Qt6
        
        self.app = QApplication(sys.argv)
        self._setup_application()
        self._check_dependencies()
        self.main_window = ControlWindow()

    def _setup_application(self):
        """Setup application properties and theme"""
        self.app.setStyle('Fusion')
        self.app.setApplicationName("Screen Translator")
        self.app.setApplicationVersion("1.0")
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon', 'icon.png')
        self.app.setWindowIcon(QIcon(icon_path))
        self._apply_dark_palette()

    def _apply_dark_palette(self):
        """Apply dark theme to the entire application"""
        dark_palette = QPalette()
        colors = {
            QPalette.ColorRole.Window: QColor(30, 30, 46),
            QPalette.ColorRole.WindowText: QColor(205, 214, 244),
            QPalette.ColorRole.Base: QColor(49, 50, 68),
            QPalette.ColorRole.AlternateBase: QColor(30, 30, 46),
            QPalette.ColorRole.ToolTipBase: QColor(30, 30, 46),
            QPalette.ColorRole.ToolTipText: QColor(205, 214, 244),
            QPalette.ColorRole.Text: QColor(205, 214, 244),
            QPalette.ColorRole.Button: QColor(49, 50, 68),
            QPalette.ColorRole.ButtonText: QColor(205, 214, 244),
            QPalette.ColorRole.BrightText: QColor(255, 255, 255),
            QPalette.ColorRole.Link: QColor(137, 180, 250),
            QPalette.ColorRole.Highlight: QColor(137, 180, 250),
            QPalette.ColorRole.HighlightedText: QColor(30, 30, 46),
        }

        for role, color in colors.items():
            dark_palette.setColor(role, color)

        self.app.setPalette(dark_palette)

    def _check_dependencies(self):
        """Check for required dependencies"""
        if not os.path.exists(Config.TESSERACT_PATH):
            QMessageBox.warning(
                None, "Tesseract OCR Missing",
                "Tesseract OCR not found. Please install it and configure the TESSERACT_PATH."
            )

        try:
            ollama.list()
        except Exception as e:
            QMessageBox.warning(
                None, "Ollama Connection Issue",
                f"Could not connect to Ollama: {e}\nPlease ensure it is installed and running."
            )

    def run(self):
        """Run the application"""
        print("Screen Translator Program Started.")
        print("Press Alt twice quickly to select screen area.")

        self.main_window.show()
        return self.app.exec()