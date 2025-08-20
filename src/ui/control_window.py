from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFrame, QDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import os

from src.config import Config
from src.utils.style_manager import StyleManager
from src.utils.ocr import OCRProcessor
from src.utils.keyboard_manager import KeyboardManager
from src.utils.workers import TranslationWorker
from src.ui.screen_selector import ScreenSelector

# Use lazy imports to avoid circular dependencies
def get_translation_overlay():
    from src.ui.translation_overlay import TranslationOverlay
    return TranslationOverlay

def get_settings_dialog():
    from src.ui.settings_dialog import SettingsDialog
    return SettingsDialog

class ControlWindow(QMainWindow):
    """Main control window"""

    def __init__(self):
        super().__init__()
        self.current_model = list(Config.AVAILABLE_MODELS.values())[0]
        self.translation_overlay = None
        self.screen_selector = None
        self.translation_worker = None

        # Initialize components
        self.ocr_processor = OCRProcessor()
        self.keyboard_manager = KeyboardManager(self.start_screen_selection)

        self._setup_window()
        self._setup_ui()
        self._center_on_screen()

        # Load settings on startup
        self._load_settings()

    def closeEvent(self, event):
        """Handle application close event and save settings"""
        try:
            # Save current settings before closing
            Config.save_settings(
                current_model=self.current_model,
                font_size=Config.DEFAULT_FONT_SIZE
            )
            print("[INFO] Settings saved on application close")
        except Exception as e:
            print(f"[ERROR] Failed to save settings on close: {e}")

        # Clean up resources
        if self.translation_overlay:
            self.translation_overlay.close()
        if self.screen_selector:
            self.screen_selector.close()
        if self.keyboard_manager:
            self.keyboard_manager.cleanup()

        event.accept()

    def _setup_window(self):
        """Configure main window"""
        self.setWindowTitle("Screen Translator")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))
        # Use DPI-aware sizing
        self.setFixedSize(
            Config.dpi_scale(Config.CONTROL_WINDOW_WIDTH), 
            Config.dpi_scale(Config.CONTROL_WINDOW_HEIGHT)
        )
        self.setStyleSheet("QMainWindow { background-color: #1e1e2e; }")

    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        # Use DPI-aware margins and spacing
        margin = Config.dpi_scale(25)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(Config.dpi_scale(20))

        self._setup_header(layout)
        self._setup_model_status(layout)
        self._setup_buttons(layout)
        self._setup_footer(layout)

    def _setup_header(self, layout):
        """Setup window header"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(Config.dpi_scale(5))

        title = QLabel("Screen Translator")
        title.setStyleSheet(f"color: #89b4fa; font: bold {Config.dpi_scale(20)}px 'Segoe UI';")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("OCR • Translation • AI")
        subtitle.setStyleSheet(f"color: #cdd6f4; font: {Config.dpi_scale(13)}px 'Segoe UI';")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

    def _setup_model_status(self, layout):
        """Setup current model status display"""
        # Current model display in single line
        current_display_name = self._get_current_model_display_name()
        self.current_model_name = QLabel(f"Current Model: {current_display_name}")
        self.current_model_name.setStyleSheet(f"color: #72f9b5; font: {Config.dpi_scale(12)}px 'Segoe UI';")
        self.current_model_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.current_model_name)

    def _get_current_model_display_name(self):
        """Get display name for current model"""
        for display_name, actual_name in Config.AVAILABLE_MODELS.items():
            if actual_name == self.current_model:
                return display_name
        return self.current_model  # Fallback to actual model name

    def _update_model_status(self):
        """Update the model status display"""
        if hasattr(self, 'current_model_name'):
            display_name = self._get_current_model_display_name()
            self.current_model_name.setText(f"Current Model: {display_name}")

    def _setup_buttons(self, layout):
        """Setup action buttons"""
        capture_btn = QPushButton("📱 Capture Screen Area")
        capture_btn.setStyleSheet(StyleManager.get_button_style(
            "#313244", "#45475a", 
            padding=f"{Config.dpi_scale(12)}px {Config.dpi_scale(20)}px", 
            font_size=Config.dpi_scale(14)
        ))
        # noinspection PyUnresolvedReferences
        capture_btn.clicked.connect(self.start_screen_selection)
        capture_btn.setMinimumHeight(Config.dpi_scale(45))

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(StyleManager.get_button_style(
            "#313244", "#45475a", 
            padding=f"{Config.dpi_scale(12)}px {Config.dpi_scale(20)}px", 
            font_size=Config.dpi_scale(14)
        ))
        # noinspection PyUnresolvedReferences
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setMinimumHeight(Config.dpi_scale(45))

        layout.addWidget(capture_btn)
        layout.addWidget(settings_btn)

    def _setup_footer(self, layout):
        """Setup window footer"""
        info_label = QLabel("💡 Press Alt twice quickly to capture")
        info_label.setStyleSheet(f"color: #6c7086; font: {Config.dpi_scale(12)}px 'Segoe UI';")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"""
            QFrame {{
                color: #45475a;
                background-color: #45475a;
                border: none;
                max-height: {Config.dpi_scale(1)}px;
            }}
        """)

        version_label = QLabel("v1.2 • AI-Powered Translation")
        version_label.setStyleSheet(f"color: #6c7086; font: {Config.dpi_scale(11)}px 'Segoe UI';")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(info_label)
        layout.addWidget(separator)
        layout.addWidget(version_label)

    def _center_on_screen(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def start_screen_selection(self):
        """Start screen area selection process"""
        # Clean up existing selector
        if self.screen_selector:
            try:
                self.screen_selector.close()
                self.screen_selector.deleteLater()
            except Exception as e:
                print(f"Error closing screen selector: {e}")

        self.screen_selector = None
        QApplication.processEvents()

        # Create new selector
        self.screen_selector = ScreenSelector()
        # noinspection PyUnresolvedReferences
        self.screen_selector.area_selected.connect(self.process_selected_area)

        QTimer.singleShot(100, self._show_screen_selector)

    def _show_screen_selector(self):
        """Show screen selector with proper timing"""
        if self.screen_selector:
            self.screen_selector.show()
            self.screen_selector.raise_()
            self.screen_selector.activateWindow()
            QTimer.singleShot(50, self.screen_selector._ensure_visibility)

    def process_selected_area(self, x, y, width, height):
        """Process the selected screen area"""
        print(f"Selected area: x={x}, y={y}, width={width}, height={height}")

        # Create or show translation overlay
        if not self.translation_overlay or not self.translation_overlay.isVisible():
            if self.translation_overlay:
                self.translation_overlay.close()
                self.translation_overlay.deleteLater()

            TranslationOverlay = get_translation_overlay()
            self.translation_overlay = TranslationOverlay()
            self.translation_overlay.show()
        else:
            self.translation_overlay.show()
            self.translation_overlay.raise_()
            self.translation_overlay.activateWindow()

        self.translation_overlay.update_text("กำลังสกัดข้อความจากภาพ...", self.current_model)
        QTimer.singleShot(300, lambda: self._capture_and_process(x, y, width, height))

    def _capture_and_process(self, x, y, width, height):
        """Capture and process the selected area"""
        try:
            QApplication.processEvents()

            # Extract text using OCR
            captured_text = self.ocr_processor.extract_text_from_area(x, y, width, height)
            print(f"[INFO] Captured Text: '{captured_text}'")

            if captured_text and not captured_text.startswith("ERROR:"):
                self.translation_overlay.update_text("กำลังแปล...", self.current_model)

                # Start translation in background
                self.translation_worker = TranslationWorker(captured_text, self.current_model)
                # noinspection PyUnresolvedReferences
                self.translation_worker.translation_finished.connect(self._on_translation_finished)
                self.translation_worker.start()
            else:
                error_msg = captured_text if captured_text.startswith("ERROR:") else "ไม่พบข้อความที่จะแปล หรือการดึงข้อความล้มเหลว"
                self.translation_overlay.update_text(error_msg, self.current_model)
        except Exception as e:
            print(f"Error in capture_and_process: {e}")
            if self.translation_overlay:
                self.translation_overlay.update_text(f"เกิดข้อผิดพลาด: {str(e)}", self.current_model)

    def _on_translation_finished(self, translated_text):
        """Handle translation completion"""
        if self.translation_overlay:
            self.translation_overlay.update_text(translated_text, self.current_model)
        print(f"[INFO] Translated Text: '{translated_text}'")

    def show_settings(self):
        """Show settings dialog"""
        SettingsDialog = get_settings_dialog()
        dialog = SettingsDialog(self.current_model, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_display_name = dialog.get_selected_model()
            self.current_model = Config.AVAILABLE_MODELS[selected_display_name]
            self._update_model_status()  # Update the model status display

            # Settings are already saved by the dialog's _save_all_settings method
            # so we don't need to save again here

            print(f"[INFO] Changed model to: {selected_display_name} ({self.current_model})")

    def _load_settings(self):
        """Load settings from file and apply to the application"""
        settings = Config.load_settings()

        # Apply settings to controls
        if 'current_model' in settings:
            self.current_model = settings['current_model']
            self._update_model_status()

        if 'default_font_size' in settings:
            font_size = settings['default_font_size']
            Config.DEFAULT_FONT_SIZE = font_size

            # Update font size in settings dialog if open
            SettingsDialog = get_settings_dialog()
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, SettingsDialog):
                    widget.current_font_size = font_size
                    widget.font_size_display.setText(f"{font_size} px")
                    break

        print(f"[INFO] Settings loaded: {settings}")