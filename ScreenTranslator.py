"""
Screen Translator Application
A modern PyQt6-based screen translation tool with OCR and AI translation capabilities.
"""

import sys
import os
import time
import keyboard
import mss
import pyperclip
from PIL import Image
import pytesseract
import ollama
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QComboBox, QFrame, QDialog,
    QMessageBox, QRubberBand, QSizePolicy, QSpinBox
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor, QPainter, QPen, QRegion


# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

class Config:
    """Application configuration"""
    # Try to find Tesseract automatically on different systems
    TESSERACT_PATHS = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows default
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',  # Windows 32-bit
        '/usr/bin/tesseract',  # Linux
        '/usr/local/bin/tesseract',  # Linux/macOS homebrew
        '/opt/homebrew/bin/tesseract',  # macOS Apple Silicon
        'tesseract'  # Try system PATH
    ]

    @classmethod
    def get_tesseract_path(cls):
        """Find the correct Tesseract path for current system"""
        import shutil

        # First try the predefined paths
        for path in cls.TESSERACT_PATHS:
            if os.path.exists(path):
                return path

        # If none found, try to find in system PATH
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            return tesseract_path

        # If still not found, return None
        return None

    # Set TESSERACT_PATH - will be initialized after class creation
    TESSERACT_PATH = None
    ALT_DOUBLE_PRESS_THRESHOLD = 0.5  # seconds

    # Model configurations
    AVAILABLE_MODELS = {
        "Gemma 3n": "gemma3n",
        "Gemma 3n (Unsloth)": "hf.co/unsloth/gemma-3n-E4B-it-GGUF:Q4_K_XL",
        #"qwen3": "qwen3:4b",
        #"phi3.5": "phi3.5:latest"
    }

    # Window settings
    OVERLAY_WIDTH = 500
    OVERLAY_HEIGHT = 200
    CONTROL_WINDOW_WIDTH = 300
    CONTROL_WINDOW_HEIGHT = 350

    # Font settings for translation overlay
    FONT_SIZES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32, 36, 48]

    # Default font settings
    DEFAULT_FONT_SIZE = 16

    # Settings file path
    SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".screen_translator_settings.json")

    @classmethod
    def load_settings(cls):
        """Load settings from file"""
        try:
            if os.path.exists(cls.SETTINGS_FILE):
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Apply loaded settings
                if 'default_font_size' in settings:
                    cls.DEFAULT_FONT_SIZE = settings['default_font_size']

                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}

    @classmethod
    def save_settings(cls, current_model=None, font_size=None):
        """Save current settings to file"""
        try:
            settings = {}

            # Load existing settings first
            if os.path.exists(cls.SETTINGS_FILE):
                try:
                    with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    settings = {}

            # Update with new values
            if current_model is not None:
                settings['current_model'] = current_model
            if font_size is not None:
                settings['default_font_size'] = font_size
                cls.DEFAULT_FONT_SIZE = font_size

            # Save to file
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            print(f"Settings saved to {cls.SETTINGS_FILE}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    @staticmethod
    def get_model_options(model_name):
        """Get specific options for each model"""
        if "unsloth" in model_name.lower() or "hf.co/unsloth" in model_name:
            return {
                'temperature': 1.0,
                'top_k': 64,
                'top_p': 0.95,
                'min_p': 0.0,
                'num_predict': 200
            }
        return {
            'temperature': 0.1,
            'num_predict': 200
        }


# =============================================================================
# STYLING AND THEMES
# =============================================================================

# Initialize Config.TESSERACT_PATH after class definition
Config.TESSERACT_PATH = Config.get_tesseract_path()

class StyleManager:
    """Centralized style management"""

    # Color palette
    COLORS = {
        'primary': '#89b4fa',
        'secondary': '#f38ba8',
        'success': '#a6e3a1',
        'warning': '#fab387',
        'error': '#f38ba8',
        'text': '#cdd6f4',
        'text_dim': '#6c7086',
        'background': '#1e1e2e',
        'surface': '#313244',
        'surface_alt': '#45475a',
        'border': '#45475a',
    }

    @classmethod
    def get_button_style(cls, bg_color, hover_color, text_color='#cdd6f4',
                        font_size=12, padding='8px 20px', border_radius='5px'):
        """Generate consistent button styles"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font: bold {font_size}px 'Segoe UI';
                padding: {padding};
                border: none;
                border-radius: {border_radius};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    @classmethod
    def get_icon_button_style(cls, color_key, size='24px', padding='4px'):
        """Generate icon button styles"""
        base_color = cls.COLORS[color_key]
        return f"""
            QPushButton {{
                background: rgba({cls._hex_to_rgb(base_color)}, 0.1);
                color: {base_color};
                border: 1px solid rgba({cls._hex_to_rgb(base_color)}, 0.3);
                border-radius: 12px;
                font: bold 12px 'Segoe UI';
                padding: {padding};
                min-width: {size};
                max-width: {size};
                min-height: {size};
                max-height: {size};
                text-align: center;
            }}
            QPushButton:hover {{
                background: rgba({cls._hex_to_rgb(base_color)}, 0.2);
                border: 1px solid rgba({cls._hex_to_rgb(base_color)}, 0.5);
            }}
            QPushButton:pressed {{
                background: rgba({cls._hex_to_rgb(base_color)}, 0.3);
            }}
        """

    @classmethod
    def get_overlay_style(cls):
        """Get main overlay frame style"""
        return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(45, 45, 68, 0.95), 
                    stop:1 rgba(30, 30, 46, 0.95));
                border: 1px solid rgba(137, 180, 250, 0.3);
                border-radius: 15px;
            }
        """

    @classmethod
    def get_text_edit_style(cls):
        """Get text edit area style"""
        return """
            QTextEdit {
                background: rgba(49, 50, 68, 0.6);
                color: #cdd6f4;
                font: 16px 'Segoe UI';
                border: 1px solid rgba(137, 180, 250, 0.2);
                border-radius: 10px;
                padding: 12px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QTextEdit:focus {
                border: 1px solid rgba(137, 180, 250, 0.4);
            }
        """ + cls._get_scrollbar_style()

    @classmethod
    def _get_scrollbar_style(cls):
        """Get scrollbar styling"""
        return """
            QScrollBar:vertical {
                background: rgba(69, 71, 90, 0.5);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(137, 180, 250, 0.6);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(137, 180, 250, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert hex color to RGB string"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"


# =============================================================================
# WORKER THREADS
# =============================================================================

class TranslationWorker(QThread):
    """Background thread for translation to keep UI responsive"""
    translation_finished = pyqtSignal(str)

    def __init__(self, text: str, model: str):
        super().__init__()
        self.text = text
        self.model = model

    def run(self):
        """Run the translation process in the background"""
        try:
            prompt = (
                f'Translate English to Thai, only provide Thai translation:\n'
                f"Provide ONLY the Thai translation, NOTHING ELSE. Do NOT explain or add any other text.\n"
                f'"{self.text}"\n\nThai Translation:'
            )

            model_options = Config.get_model_options(self.model)
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options=model_options
            )

            translated_text = response['response'].strip()

            # Validate Thai characters
            if not any('\u0e00' <= char <= '\u0e7f' for char in translated_text):
                result = f"Translation Error: ตัวอักษรไม่ถูกต้อง\n\nOriginal response: {translated_text}"
            else:
                result = translated_text

        except Exception as e:
            result = f"Translation Error: {e}"

        # noinspection PyUnresolvedReferences
        self.translation_finished.emit(result)


# =============================================================================
# UTILITY CLASSES
# =============================================================================

class OCRProcessor:
    """Handles OCR operations"""

    def __init__(self):
        self._initialize_tesseract()

    def _initialize_tesseract(self):
        """Initialize Tesseract OCR"""
        if os.path.exists(Config.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
        else:
            print(f"Warning: Tesseract not found at {Config.TESSERACT_PATH}")

    def extract_text_from_area(self, x, y, width, height):
        """Extract text from screen area using OCR"""
        try:
            with mss.mss() as sct:
                # Ensure coordinates are valid
                x, y = max(0, int(x)), max(0, int(y))
                width, height = max(1, int(width)), max(1, int(height))

                monitor = {"top": y, "left": x, "width": width, "height": height}
                screenshot = sct.grab(monitor)

                # Convert to PIL Image and grayscale for better OCR
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img = img.convert('L')

                # Try different OCR settings
                text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
                if not text.strip():
                    text = pytesseract.image_to_string(img, lang='eng', config='--psm 3')

                return text.strip()

        except pytesseract.pytesseract.TesseractNotFoundError:
            return "ERROR: Tesseract OCR not installed or not in PATH"
        except Exception as e:
            return f"ERROR: {str(e)}"


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


# =============================================================================
# UI COMPONENTS
# =============================================================================

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


# =============================================================================
# MAIN UI CLASSES
# =============================================================================

class ScreenSelector(QWidget):
    """Full-screen overlay for area selection"""
    area_selected = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__(None)
        self._setup_window()
        self._setup_variables()
        self._setup_ui()
        self._setup_timers()

    def _setup_window(self):
        """Configure window properties"""
        # Calculate total screen area
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(total_rect)

    def _setup_variables(self):
        """Initialize instance variables"""
        self.origin = QPoint()
        self.current_rect = QRect()
        self.is_selecting = False
        self.bg_color = QColor(0, 0, 0, 200)

    def _setup_ui(self):
        """Setup UI components"""
        # Rubber band for selection
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 255, 60))
        self.rubber_band.setPalette(palette)

        # Instructions label
        self.instructions = QLabel("Click and drag to select area. Press ESC to cancel.", self)
        self.instructions.setStyleSheet("""
            QLabel {
                color: white;
                font: bold 14px 'Segoe UI';
                background: rgba(0, 0, 0, 180);
                border-radius: 10px;
                padding: 10px 20px;
            }
        """)
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instructions.resize(400, 50)

    def _setup_timers(self):
        """Setup initialization timers"""
        QTimer.singleShot(100, self._position_instructions)
        QTimer.singleShot(50, self._ensure_visibility)

    def _position_instructions(self):
        """Position instructions at screen center"""
        primary_screen = QApplication.primaryScreen()
        center_x = primary_screen.geometry().center().x()
        self.instructions.move(center_x - self.instructions.width() // 2, 30)

    def _ensure_visibility(self):
        """Ensure window is visible and on top"""
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        """Draw overlay with transparent selection area"""
        painter = QPainter(self)
        mask = QRegion(self.rect())

        if self.is_selecting and not self.current_rect.isEmpty():
            mask = mask.subtracted(QRegion(self.current_rect))

        painter.setClipRegion(mask)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawRect(self.rect())
        painter.setClipping(False)

        if self.is_selecting and not self.current_rect.isEmpty():
            pen = QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.current_rect)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        event.accept()

    def mousePressEvent(self, event):
        """Handle mouse press to start selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = True
            self.origin = event.position().toPoint()
            self.current_rect = QRect(self.origin, QSize(1, 1))
            self.rubber_band.setGeometry(self.current_rect)
            self.rubber_band.show()
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update selection"""
        if self.is_selecting:
            current_pos = event.position().toPoint()
            self.current_rect = QRect(self.origin, current_pos).normalized()
            self.rubber_band.setGeometry(self.current_rect)
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            final_rect = self.current_rect
            self.rubber_band.hide()

            if final_rect.width() > 10 and final_rect.height() > 10:
                QTimer.singleShot(100, lambda: self._emit_selection(final_rect))
            else:
                self.close()

    def _emit_selection(self, rect):
        """Emit selection signal and close"""
        # noinspection PyUnresolvedReferences
        self.area_selected.emit(rect.x(), rect.y(), rect.width(), rect.height())
        self.close()


class TranslationOverlay(QWidget):
    """Modern floating translation window"""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_variables()
        self.setup_ui()
        self._setup_animations()

    def _setup_window(self):
        """Configure window properties"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Position near top-right corner
        screen = QApplication.primaryScreen().geometry()
        self.resize(Config.OVERLAY_WIDTH, Config.OVERLAY_HEIGHT)
        self.move(screen.width() - Config.OVERLAY_WIDTH - 20, 50)

    def _setup_variables(self):
        """Initialize instance variables"""
        # Drag functionality
        self.drag_start_position = None
        self.is_dragging = False

        # Resize functionality
        self.resize_start_position = None
        self.resize_start_geometry = None
        self.is_resizing = False
        self.resize_edge = None
        self.resize_margin = 15

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet(StyleManager.get_overlay_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)

        # Inner layout
        inner_layout = QVBoxLayout(self.main_frame)
        inner_layout.setContentsMargins(20, 15, 20, 15)
        inner_layout.setSpacing(12)

        # Setup sections
        self._setup_header(inner_layout)
        self._setup_content(inner_layout)
        self._setup_footer(inner_layout)

    def _setup_header(self, layout):
        """Setup header with title and controls"""
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.header_frame.setFixedHeight(40)
        self.header_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Title section
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)

        icon_label = QLabel("🌐")
        icon_label.setStyleSheet("font-size: 18px; color: #89b4fa;")

        # Store reference to title label for easy updates
        self.title_label = QLabel("Translation")
        self.title_label.setStyleSheet("color: #cdd6f4; font: bold 14px 'Segoe UI';")

        drag_hint = QLabel("• • •")
        drag_hint.setStyleSheet("color: rgba(205, 214, 244, 0.5); font: bold 12px 'Segoe UI';")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(drag_hint)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Control buttons
        self._setup_control_buttons(header_layout)
        layout.addWidget(self.header_frame)

    def _setup_control_buttons(self, layout):
        """Setup settings and close buttons"""
        # Settings button
        settings_btn = QPushButton("⚙️")
        settings_btn.setStyleSheet(StyleManager.get_icon_button_style('primary'))
        settings_btn.setToolTip("Settings")
        # noinspection PyUnresolvedReferences
        settings_btn.clicked.connect(self._show_settings)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(StyleManager.get_icon_button_style('secondary'))
        # noinspection PyUnresolvedReferences
        close_btn.clicked.connect(self.close)

        layout.addWidget(settings_btn)
        layout.addWidget(close_btn)

    def _setup_content(self, layout):
        """Setup content area"""
        self.translation_text = QTextEdit()
        self.translation_text.setStyleSheet(StyleManager.get_text_edit_style())
        self.translation_text.setReadOnly(True)
        self.translation_text.setMinimumHeight(60)
        self.translation_text.setMaximumHeight(1500)
        layout.addWidget(self.translation_text)

    def _setup_footer(self, layout):
        """Setup footer with status indicators"""
        self.footer_frame = QFrame()
        self.footer_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.footer_frame.setFixedHeight(30)
        self.footer_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(10)

        # Status and copy indicators
        self.status_indicator = StatusIndicator()
        self.copy_indicator = CopyIndicator()

        footer_layout.addWidget(self.status_indicator)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_indicator)
        layout.addWidget(self.footer_frame)

    def _setup_animations(self):
        """Setup entrance animations"""
        # เริ่มต้นด้วยการซ่อน widget
        self.setWindowOpacity(0.0)

        # เก็บตำแหน่งเดิมไว้
        self.original_pos = self.pos()

        # ตั้งตำแหน่งเริ่มต้นสำหรับ slide animation
        start_pos = QPoint(self.original_pos.x(), self.original_pos.y() - 30)
        self.move(start_pos)

        # Fade-in animation (ใช้ window opacity แทน graphics effect)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide-in animation
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(400)
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(self.original_pos)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Scale animation สำหรับเอฟเฟค "pop-in"
        self.scale_animation = QPropertyAnimation(self, b"size")
        self.scale_animation.setDuration(400)

        # เริ่มจากขนาดเล็กกว่าเล็กน้อย
        start_size = QSize(int(self.width() * 0.95), int(self.height() * 0.95))
        end_size = self.size()

        self.scale_animation.setStartValue(start_size)
        self.scale_animation.setEndValue(end_size)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)

        # เริ่มอนิเมชันพร้อมกัน
        QTimer.singleShot(50, self._start_animations)

    def _start_animations(self):
        """เริ่มอนิเมชันทั้งหมด"""
        self.fade_animation.start()
        self.slide_animation.start()
        self.scale_animation.start()

    def update_text(self, text, current_model=None):
        """Update translation text and copy to clipboard"""
        self.translation_text.setPlainText(text)
        pyperclip.copy(text)
        self.copy_indicator.show_briefly()

        # Update model display in header if provided
        if current_model:
            self._update_model_display(current_model)

        # Update status based on content
        if text.startswith("กำลัง"):
            self.status_indicator.update_status("Processing...", 'warning')
        elif text.startswith("Translation Error"):
            self.status_indicator.update_status("Error", 'error')
        else:
            self.status_indicator.update_status("Completed", 'success')

    def _update_model_display(self, current_model):
        """Update the model display in header"""
        # Get display name for the model
        display_name = None
        for name, model in Config.AVAILABLE_MODELS.items():
            if model == current_model:
                display_name = name
                break

        if not display_name:
            display_name = current_model

        # Update the title label directly using stored reference
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"Translation • {display_name}")

    def _show_settings(self):
        """Show settings dialog"""
        # Get the main window to access current model and settings
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ControlWindow):
                main_window = widget
                break

        if main_window:
            # Create and show settings dialog
            dialog = SettingsDialog(main_window.current_model, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_display_name = dialog.get_selected_model()
                main_window.current_model = Config.AVAILABLE_MODELS[selected_display_name]
                main_window._update_model_status()  # Update the model status display

                # Update the overlay header immediately
                self._update_model_display(main_window.current_model)

                print(f"[INFO] Changed model to: {selected_display_name} ({main_window.current_model})")
        else:
            # Fallback if main window not found
            dialog = SettingsDialog(list(Config.AVAILABLE_MODELS.values())[0], self)
            dialog.exec()

    # Mouse event handlers for drag and resize functionality
    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.MouseButton.LeftButton:
            click_pos = event.position().toPoint()

            # Check for resize edge first
            resize_edge = self._get_resize_edge(click_pos)
            if resize_edge:
                self.is_resizing = True
                self.resize_edge = resize_edge
                self.resize_start_position = event.globalPosition().toPoint()
                self.resize_start_geometry = self.geometry()
                return

            # Check if click is on header for dragging
            header_rect = self.header_frame.geometry()
            if header_rect.contains(click_pos):
                self.is_dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and resizing"""
        if self.is_resizing:
            self._perform_resize(event.globalPosition().toPoint())
        elif self.is_dragging and self.drag_start_position is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.drag_start_position = None
            self.resize_start_position = None
            self.resize_start_geometry = None
            self.resize_edge = None

    def _get_resize_edge(self, pos):
        """Determine which edge/corner is being clicked for resizing"""
        rect = self.rect()
        margin = self.resize_margin

        # Check corners first
        if pos.x() <= margin and pos.y() <= margin:
            return "top-left"
        elif pos.x() >= rect.width() - margin and pos.y() <= margin:
            return "top-right"
        elif pos.x() <= margin and pos.y() >= rect.height() - margin:
            return "bottom-left"
        elif pos.x() >= rect.width() - margin and pos.y() >= rect.height() - margin:
            return "bottom-right"
        # Check edges
        elif pos.y() <= margin:
            return "top"
        elif pos.y() >= rect.height() - margin:
            return "bottom"
        elif pos.x() <= margin:
            return "left"
        elif pos.x() >= rect.width() - margin:
            return "right"

        return None

    def _perform_resize(self, global_pos):
        """Perform the actual resizing based on the edge being dragged"""
        if not self.is_resizing or not self.resize_edge:
            return

        diff = global_pos - self.resize_start_position
        original_geometry = self.resize_start_geometry

        new_x = original_geometry.x()
        new_y = original_geometry.y()
        new_width = original_geometry.width()
        new_height = original_geometry.height()

        # Apply resize based on edge
        if "left" in self.resize_edge:
            new_x = original_geometry.x() + diff.x()
            new_width = original_geometry.width() - diff.x()
        elif "right" in self.resize_edge:
            new_width = original_geometry.width() + diff.x()

        if "top" in self.resize_edge:
            new_y = original_geometry.y() + diff.y()
            new_height = original_geometry.height() - diff.y()
        elif "bottom" in self.resize_edge:
            new_height = original_geometry.height() + diff.y()

        # Apply size constraints
        min_width, min_height = 500, 150
        max_width, max_height = 1200, 1500

        # Get screen boundaries
        screen_rect = QApplication.primaryScreen().geometry()
        screen_left = screen_rect.left()
        screen_top = screen_rect.top()
        screen_right = screen_rect.right()
        screen_bottom = screen_rect.bottom()

        # Apply width constraints and position limits
        if new_width < min_width:
            if "left" in self.resize_edge:
                # Don't allow the window to shrink beyond min_width
                new_x = original_geometry.right() - min_width
                new_width = min_width
            else:
                new_width = min_width
        elif new_width > max_width:
            if "left" in self.resize_edge:
                new_x = original_geometry.right() - max_width
                new_width = max_width
            else:
                new_width = max_width

        # Apply height constraints and position limits
        if new_height < min_height:
            if "top" in self.resize_edge:
                # Don't allow the window to shrink beyond min_height
                new_y = original_geometry.bottom() - min_height
                new_height = min_height
            else:
                new_height = min_height
        elif new_height > max_height:
            if "top" in self.resize_edge:
                new_y = original_geometry.bottom() - max_height
                new_height = max_height
            else:
                new_height = max_height

        # Prevent window from going outside screen boundaries
        # Left boundary check
        if new_x < screen_left:
            if "left" in self.resize_edge:
                # Adjust width to compensate for position constraint
                new_width = new_width - (screen_left - new_x)
                new_x = screen_left
            else:
                new_x = screen_left

        # Top boundary check
        if new_y < screen_top:
            if "top" in self.resize_edge:
                # Adjust height to compensate for position constraint
                new_height = new_height - (screen_top - new_y)
                new_y = screen_top
            else:
                new_y = screen_top

        # Right boundary check
        if new_x + new_width > screen_right:
            if "right" in self.resize_edge:
                new_width = screen_right - new_x
            else:
                new_x = screen_right - new_width

        # Bottom boundary check
        if new_y + new_height > screen_bottom:
            if "bottom" in self.resize_edge:
                new_height = screen_bottom - new_y
            else:
                new_y = screen_bottom - new_height

        # Final validation to ensure minimum size is maintained
        new_width = max(min_width, new_width)
        new_height = max(min_height, new_height)

        self.setGeometry(new_x, new_y, new_width, new_height)


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    def __init__(self, current_model, parent=None):
        super().__init__(parent)
        self.current_model = current_model
        self._setup_dialog()
        self._setup_ui()
        self._center_on_screen()

    def _setup_dialog(self):
        """Configure dialog properties"""
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("QDialog { background-color: #1e1e2e; color: #cdd6f4; }")

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        self._setup_header(layout)

        # Model selection
        self._setup_model_selection(layout)

        # Font customization section
        self._setup_font_section(layout)

        layout.addStretch()

        # Buttons
        self._setup_buttons(layout)

    def _setup_header(self, layout):
        """Setup dialog header"""
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("color: #89b4fa; font: bold 18px 'Segoe UI';")

        subtitle = QLabel("Configure your AI model and preferences")
        subtitle.setStyleSheet("color: #cdd6f4; font: 12px 'Segoe UI'; margin-top: 3px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #45475a;
                background-color: #45475a;
                border: none;
                max-height: 1px;
                margin: 3px 0px;
            }
        """)
        layout.addWidget(separator)

    def _setup_model_selection(self, layout):
        """Setup model selection UI"""
        model_label = QLabel("🤖 Ollama Model:")
        model_label.setStyleSheet("color: #cdd6f4; font: bold 13px 'Segoe UI'; margin-top: 5px;")

        self.model_combo = QComboBox()
        self.model_combo.addItems(Config.AVAILABLE_MODELS.keys())

        # Set current model
        current_display_name = self._find_display_name()
        if current_display_name:
            self.model_combo.setCurrentText(current_display_name)

        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #45475a;
                color: #cdd6f4;
                font: 12px 'Segoe UI';
                padding: 6px;
                border: none;
                border-radius: 5px;
                min-height: 28px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox QAbstractItemView {
                background-color: #45475a;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                padding: 8px;
                border: none;
            }
        """)

        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)

    def _setup_font_section(self, layout):
        """Setup font customization section"""
        font_label = QLabel("🔤 Font Customization:")
        font_label.setStyleSheet("color: #cdd6f4; font: bold 13px 'Segoe UI'; margin-top: 5px;")

        # Create a horizontal layout for font controls
        font_controls_layout = QHBoxLayout()
        font_controls_layout.setSpacing(10)

        # Font size label with icon - positioned on the left
        size_label = QLabel("Size:")
        size_label.setStyleSheet("""
            QLabel {
                color: #89b4fa;
                font: bold 12px 'Segoe UI';
                padding: 5px;
            }
        """)

        # Add the size label to the left
        font_controls_layout.addWidget(size_label)

        # Add stretch to push the controls to the right
        font_controls_layout.addStretch()

        # Create a container for the font size display controls (right side)
        font_display_container = QHBoxLayout()
        font_display_container.setSpacing(8)

        # Font size display (same style as model combo)
        self.font_size_display = QLabel(f"{Config.DEFAULT_FONT_SIZE} px")
        self.font_size_display.setStyleSheet("""
            QLabel {
                background-color: #45475a;
                color: #cdd6f4;
                font: 12px 'Segoe UI';
                padding: 13px 6px;
                border: none;
                border-radius: 5px;
                min-height: 16px;
                max-height: 16px;
                min-width: 50px;
            }
        """)
        self.font_size_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create up/down arrow buttons
        self.font_size_up_btn = QPushButton("▲")
        self.font_size_up_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #89b4fa, stop:1 #74c7ec);
                color: #1e1e2e;
                font: bold 10px 'Segoe UI';
                border: none;
                border-radius: 3px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a6d4ff, stop:1 #89b4fa);
            }
            QPushButton:pressed {
                background: #6fa8dc;
            }
        """)

        self.font_size_down_btn = QPushButton("▼")
        self.font_size_down_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74c7ec, stop:1 #89b4fa);
                color: #1e1e2e;
                font: bold 10px 'Segoe UI';
                border: none;
                border-radius: 3px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #89b4fa, stop:1 #a6d4ff);
            }
            QPushButton:pressed {
                background: #6fa8dc;
            }
        """)

        # Connect button signals
        # noinspection PyUnresolvedReferences
        self.font_size_up_btn.clicked.connect(self._increase_font_size)
        # noinspection PyUnresolvedReferences
        self.font_size_down_btn.clicked.connect(self._decrease_font_size)

        # Store current font size
        self.current_font_size = Config.DEFAULT_FONT_SIZE

        # Create vertical layout for arrow buttons
        arrow_layout = QVBoxLayout()
        arrow_layout.setSpacing(2)
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.addWidget(self.font_size_up_btn)
        arrow_layout.addWidget(self.font_size_down_btn)

        # Add font display and arrow buttons to the display container
        font_display_container.addWidget(self.font_size_display)
        font_display_container.addLayout(arrow_layout)

        # Add the display container to the main layout
        font_controls_layout.addLayout(font_display_container)

        layout.addWidget(font_label)
        layout.addLayout(font_controls_layout)

    def _increase_font_size(self):
        """Increase font size"""
        if self.current_font_size < 48:  # Max size
            self.current_font_size += 1
            self._update_font_display()

    def _decrease_font_size(self):
        """Decrease font size"""
        if self.current_font_size > 8:  # Min size
            self.current_font_size -= 1
            self._update_font_display()

    def _update_font_display(self):
        """Update the font size display"""
        self.font_size_display.setText(f"{self.current_font_size} px")

    def _setup_buttons(self, layout):
        """Setup dialog buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(StyleManager.get_button_style("#313244", "#45475a"))
        # noinspection PyUnresolvedReferences
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumSize(100, 40)

        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet(StyleManager.get_button_style("#89b4fa", "#74c7ec", "#1e1e2e"))
        # noinspection PyUnresolvedReferences
        save_btn.clicked.connect(self._save_all_settings)
        save_btn.setMinimumSize(150, 40)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

    def _save_all_settings(self):
        """Save all settings including model and font size"""
        # Get selected model
        selected_display_name = self.get_selected_model()
        selected_model = Config.AVAILABLE_MODELS[selected_display_name]

        # Apply font settings first
        self._apply_font_settings()

        # Save settings to file
        Config.save_settings(
            current_model=selected_model,
            font_size=self.current_font_size
        )

        # Then accept the dialog (which will handle model changes)
        self.accept()

    def _find_display_name(self):
        """Find display name for current model"""
        for display_name, actual_name in Config.AVAILABLE_MODELS.items():
            if actual_name == self.current_model:
                return display_name
        return None

    def _center_on_screen(self):
        """Center dialog on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def get_selected_model(self):
        """Get the selected model name"""
        return self.model_combo.currentText()

    def _apply_font_settings(self):
        """Apply the selected font settings"""
        selected_size = self.current_font_size  # Use the custom font size instead of spinbox

        # Update the configuration (this could be saved to a file or applied globally)
        Config.DEFAULT_FONT_SIZE = selected_size

        # Update the translation overlay if it's open
        if self.parent() and hasattr(self.parent(), 'translation_text'):
            # Apply new font size to the translation text area specifically
            self.parent().translation_text.setStyleSheet(f"""
                QTextEdit {{
                    background: rgba(49, 50, 68, 0.6);
                    color: #cdd6f4;
                    font: {selected_size}px 'Segoe UI';
                    border: 1px solid rgba(137, 180, 250, 0.2);
                    border-radius: 10px;
                    padding: 12px;
                    selection-background-color: #89b4fa;
                    selection-color: #1e1e2e;
                }}
                QTextEdit:focus {{
                    border: 1px solid rgba(137, 180, 250, 0.4);
                }}
                QScrollBar:vertical {{
                    background: rgba(69, 71, 90, 0.5);
                    width: 8px;
                    border-radius: 4px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: rgba(137, 180, 250, 0.6);
                    border-radius: 4px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: rgba(137, 180, 250, 0.8);
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
        else:
            # Try to find the translation overlay globally
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, TranslationOverlay) and hasattr(widget, 'translation_text'):
                    widget.translation_text.setStyleSheet(f"""
                        QTextEdit {{
                            background: rgba(49, 50, 68, 0.6);
                            color: #cdd6f4;
                            font: {selected_size}px 'Segoe UI';
                            border: 1px solid rgba(137, 180, 250, 0.2);
                            border-radius: 10px;
                            padding: 12px;
                            selection-background-color: #89b4fa;
                            selection-color: #1e1e2e;
                        }}
                        QTextEdit:focus {{
                            border: 1px solid rgba(137, 180, 250, 0.4);
                        }}
                        QScrollBar:vertical {{
                            background: rgba(69, 71, 90, 0.5);
                            width: 8px;
                            border-radius: 4px;
                            margin: 0px;
                        }}
                        QScrollBar::handle:vertical {{
                            background: rgba(137, 180, 250, 0.6);
                            border-radius: 4px;
                            min-height: 20px;
                        }}
                        QScrollBar::handle:vertical:hover {{
                            background: rgba(137, 180, 250, 0.8);
                        }}
                        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                            height: 0px;
                        }}
                    """)
                    break

        print(f"[INFO] Font settings applied: Size: {selected_size}")


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
        self.setFixedSize(Config.CONTROL_WINDOW_WIDTH, Config.CONTROL_WINDOW_HEIGHT)
        self.setStyleSheet("QMainWindow { background-color: #1e1e2e; }")

    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        self._setup_header(layout)
        self._setup_model_status(layout)
        self._setup_buttons(layout)
        self._setup_footer(layout)

    def _setup_header(self, layout):
        """Setup window header"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title = QLabel("Screen Translator")
        title.setStyleSheet("color: #89b4fa; font: bold 20px 'Segoe UI';")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("OCR • Translation • AI")
        subtitle.setStyleSheet("color: #cdd6f4; font: 13px 'Segoe UI';")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

    def _setup_model_status(self, layout):
        """Setup current model status display"""
        # Current model display in single line
        current_display_name = self._get_current_model_display_name()
        self.current_model_name = QLabel(f"Current Model: {current_display_name}")
        self.current_model_name.setStyleSheet("color: #72f9b5; font: 12px 'Segoe UI';")
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
            "#313244", "#45475a", padding="12px 20px", font_size=14
        ))
        # noinspection PyUnresolvedReferences
        capture_btn.clicked.connect(self.start_screen_selection)
        capture_btn.setMinimumHeight(45)

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(StyleManager.get_button_style(
            "#313244", "#45475a", padding="12px 20px", font_size=14
        ))
        # noinspection PyUnresolvedReferences
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setMinimumHeight(45)

        layout.addWidget(capture_btn)
        layout.addWidget(settings_btn)

    def _setup_footer(self, layout):
        """Setup window footer"""
        info_label = QLabel("💡 Press Alt twice quickly to capture")
        info_label.setStyleSheet("color: #6c7086; font: 12px 'Segoe UI';")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #45475a;
                background-color: #45475a;
                border: none;
                max-height: 1px;
            }
        """)

        version_label = QLabel("v1.0 • AI-Powered Translation")
        version_label.setStyleSheet("color: #6c7086; font: 11px 'Segoe UI';")
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
        dialog = SettingsDialog(self.current_model, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_display_name = dialog.get_selected_model()
            self.current_model = Config.AVAILABLE_MODELS[selected_display_name]
            self._update_model_status()  # Update the model status display

            # Settings are already saved by the dialog's _save_all_settings method
            # so we don't need to save again here

            print(f"[INFO] Changed model to: {selected_display_name} ({self.current_model})")

    def closeEvent(self, event):
        """Handle application closing"""
        # Save current settings before closing
        try:
            Config.save_settings(
                current_model=self.current_model,
                font_size=getattr(self, 'current_font_size', Config.DEFAULT_FONT_SIZE)
            )
            print("[INFO] Settings saved before closing")
        except Exception as e:
            print(f"[WARNING] Failed to save settings: {e}")

        self.keyboard_manager.cleanup()
        if self.translation_overlay:
            self.translation_overlay.close()
        event.accept()

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
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, SettingsDialog):
                    widget.current_font_size = font_size
                    widget.font_size_display.setText(f"{font_size} px")
                    break

        print(f"[INFO] Settings loaded: {settings}")


# =============================================================================
# APPLICATION CLASS
# =============================================================================

class ScreenTranslatorApp:
    """Main application class"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self._setup_application()
        self._check_dependencies()
        self.main_window = ControlWindow()

    def _setup_application(self):
        """Setup application properties and theme"""
        self.app.setStyle('Fusion')
        self.app.setApplicationName("Screen Translator")
        self.app.setApplicationVersion("1.0")
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


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    sys.exit(app.run())
