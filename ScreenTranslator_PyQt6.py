import sys
import keyboard
import mss
from PIL import Image
import pytesseract
import ollama
import pyperclip
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QTextEdit,
                           QComboBox, QFrame, QDialog, QMessageBox,
                           QRubberBand, QSizeGrip)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QCursor, QPen, QScreen, QRegion
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# --- Constants and Configuration ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
AVAILABLE_MODELS = ["gemma3n"]
ALT_DOUBLE_PRESS_THRESHOLD = 0.5  # seconds

class TranslationWorker(QThread):
    """Background thread for translation to keep UI responsive"""
    translation_finished = pyqtSignal(str)

    def __init__(self, text, model):
        super().__init__()
        self.text = text
        self.model = model

    def run(self):
        try:
            prompt = f'แปลข้อความต่อไปนี้เป็นภาษาไทย โดยไม่ต้องอธิบายหรือแปลความหมายเพิ่มเติม):\n"{self.text}"\n\nThai Translation:'
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.1, 'num_predict': 200}
            )
            translated_text = response['response'].strip()
            if not any('\u0e00' <= char <= '\u0e7f' for char in translated_text):
                result = f"Translation Error: ตัวอักษรไม่ถูกต้อง\n\nOriginal response: {translated_text}"
            else:
                result = translated_text
        except Exception as e:
            result = f"Translation Error: {e}"

        self.translation_finished.emit(result)

class ScreenSelector(QWidget):
    """Full-screen overlay for area selection"""
    area_selected = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__(None)  # Create as a top-level window without parent

        # Get information about all screens
        self.screens = QApplication.screens()

        # Calculate the bounding rectangle of all screens
        total_rect = QRect()
        for screen in self.screens:
            screen_geometry = screen.geometry()
            total_rect = total_rect.united(screen_geometry)

        # Configure window for full coverage of all screens
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set geometry to cover all screens
        self.setGeometry(total_rect)

        # Initialize variables
        self.origin = QPoint()
        self.current_rect = QRect()
        self.is_selecting = False
        self.bg_color = QColor(0, 0, 0, 200)  # Dark semi-transparent background

        # Create rubber band for selection (adding this back)
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        rubber_band_palette = QPalette()
        rubber_band_palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 255, 60))
        self.rubber_band.setPalette(rubber_band_palette)

        # Create instructions label
        self.instructions = QLabel("คลิกและลากเพื่อเลือกพื้นที่ กด ESC เพื่อยกเลิก", self)
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

        # Position the instructions - delay to ensure window is shown
        QTimer.singleShot(100, self.position_instructions)

        # Make sure the window appears on top and in front
        QTimer.singleShot(50, self.ensure_visibility)

    def ensure_visibility(self):
        """Make sure the window is visible and on top"""
        self.raise_()
        self.activateWindow()

    def position_instructions(self):
        """Position the instructions at the top center of the screen"""
        primary_screen = QApplication.primaryScreen()
        screen_size = primary_screen.size()
        screen_center_x = primary_screen.geometry().center().x()
        self.instructions.move(screen_center_x - self.instructions.width() // 2, 30)

    def paintEvent(self, event):
        """Draw the semi-transparent background with completely transparent selection area"""
        painter = QPainter(self)

        # Create a mask for the entire screen area
        mask = QRegion(self.rect())

        # If selecting, remove the selection rectangle from the mask
        if self.is_selecting and not self.current_rect.isEmpty():
            # Subtract the selection rectangle from the mask
            mask = mask.subtracted(QRegion(self.current_rect))

        # Set clipping to our mask (this will only draw in the masked areas)
        painter.setClipRegion(mask)

        # Draw the semi-transparent dark overlay only on the masked area
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawRect(self.rect())

        # Reset clipping to draw the border around the selection
        painter.setClipping(False)

        # If selecting, draw only a border around the selection area
        if self.is_selecting and not self.current_rect.isEmpty():
            # Draw only the border with a solid white line
            pen = QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill = completely transparent
            painter.drawRect(self.current_rect)

        painter.end()

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        event.accept()

    def mousePressEvent(self, event):
        """Handle mouse press events to start selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = True
            self.origin = event.position().toPoint()
            self.current_rect = QRect(self.origin, QSize(1, 1))
            # Update the rubber band
            self.rubber_band.setGeometry(self.current_rect)
            self.rubber_band.show()
            self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events to update selection"""
        if self.is_selecting:
            # Calculate selection rectangle and update
            current_pos = event.position().toPoint()
            self.current_rect = QRect(self.origin, current_pos).normalized()
            # Update the rubber band
            self.rubber_band.setGeometry(self.current_rect)
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            final_rect = self.current_rect
            # Hide the rubber band
            self.rubber_band.hide()

            # Ensure selection is valid
            if final_rect.width() > 10 and final_rect.height() > 10:
                # Use single-shot timer to let UI update before proceeding
                QTimer.singleShot(100, lambda: self.emit_selection(final_rect))
            else:
                self.close()
        event.accept()

    def emit_selection(self, rect):
        """Emit the selected area signal and close the selector"""
        self.area_selected.emit(rect.x(), rect.y(), rect.width(), rect.height())
        self.close()

    def showEvent(self, event):
        """Make sure we're truly fullscreen when shown"""
        super().showEvent(event)
        # Recalculate the geometry to ensure we cover all screens
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())
        self.setGeometry(total_rect)

class TranslationOverlay(QWidget):
    """Resizable floating translation window"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Window properties
        self.resize(600, 300)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 700, 100)  # Position near right edge of screen

        # Enable mouse tracking for resize areas
        self.setMouseTracking(True)
        #self.setAttribute(Qt.WA_TranslucentBackground)

        # Drag and resize variables
        self.drag_start_position = None
        self.resize_mode = None
        self.resize_margin = 8
        self.resize_ghost = None  # For smooth resize visual feedback

        self.setup_ui()

    def setup_ui(self):
        # Main container with rounded corners and shadow
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border: 2px solid #45475a;
                border-radius: 10px;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)

        # Inner layout
        inner_layout = QVBoxLayout(self.main_frame)
        inner_layout.setContentsMargins(8, 8, 8, 8)
        inner_layout.setSpacing(0)

        # Header
        self.setup_header(inner_layout)

        # Content area
        self.translation_text = QTextEdit()
        self.translation_text.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                font: 14px 'Segoe UI';
                border: none;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        self.translation_text.setReadOnly(True)
        inner_layout.addWidget(self.translation_text)

        # Footer
        self.setup_footer(inner_layout)

    def setup_header(self, layout):
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-radius: 5px;
                max-height: 40px;
                min-height: 40px;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        # Drag handle
        drag_label = QLabel("⋮⋮")
        drag_label.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: bold 16px 'Segoe UI';
                padding: 8px;
            }
        """)
        header_layout.addWidget(drag_label)

        # Title
        title = QLabel("🌐 Translation")
        title.setStyleSheet("""
            QLabel {
                color: #89b4fa;
                font: bold 13px 'Segoe UI';
                padding: 8px;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Control buttons
        settings_btn = QPushButton("⚙")
        settings_btn.setStyleSheet(self.get_button_style("#fab387"))
        settings_btn.setFixedSize(30, 30)
        settings_btn.clicked.connect(self.show_settings)

        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(self.get_button_style("#f38ba8"))
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)

        header_layout.addWidget(settings_btn)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

    def setup_footer(self, layout):
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                max-height: 30px;
                min-height: 30px;
            }
        """)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 4, 12, 4)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6c7086;
                font: 11px 'Segoe UI';
            }
        """)

        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()

        layout.addWidget(footer)

    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 3px;
                font: bold 13px 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """

    def show_settings(self):
        # Emit signal to parent to show settings
        if hasattr(self.parent(), 'show_settings'):
            self.parent().show_settings()

    def update_text(self, text):
        self.translation_text.setPlainText(text)
        pyperclip.copy(text)

    def update_status(self, status):
        self.status_label.setText(status)
        if "Resized" in status:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    # Mouse events for dragging and resizing
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()

            # Check if we're in a resize area
            pos = event.position().toPoint()
            self.resize_mode = self.get_resize_mode(pos)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_start_position:
            if self.resize_mode:
                self.handle_resize(event.globalPosition().toPoint())
            else:
                # Dragging
                diff = event.globalPosition().toPoint() - self.drag_start_position
                new_pos = self.pos() + diff
                self.move(new_pos)
                self.drag_start_position = event.globalPosition().toPoint()
        else:
            # Update cursor based on position
            self.update_cursor(pos)

    def mouseReleaseEvent(self, event):
        # Apply final size when mouse released and clean up ghost
        if self.resize_mode and self.resize_ghost:
            # Get final size from ghost
            final_size = self.resize_ghost.size()
            self.resize(final_size.width(), final_size.height())

            # Clean up ghost
            self.resize_ghost.close()
            self.resize_ghost.deleteLater()
            self.resize_ghost = None

            self.update_status(f"Resized to {final_size.width()}x{final_size.height()}")

        self.drag_start_position = None
        self.resize_mode = None

    def get_resize_mode(self, pos):
        """Determine resize mode based on mouse position"""
        rect = self.rect()
        margin = self.resize_margin

        right_edge = pos.x() >= rect.width() - margin
        bottom_edge = pos.y() >= rect.height() - margin

        if right_edge and bottom_edge:
            return "corner"
        elif right_edge:
            return "right"
        elif bottom_edge:
            return "bottom"
        return None

    def update_cursor(self, pos):
        """Update cursor based on mouse position"""
        mode = self.get_resize_mode(pos)

        if mode == "corner":
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif mode == "right":
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif mode == "bottom":
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def handle_resize(self, global_pos):
        """Handle window resizing with smoother visual feedback"""
        if not self.resize_mode:
            return

        diff = global_pos - self.drag_start_position
        current_size = self.size()
        new_width = current_size.width()
        new_height = current_size.height()

        if self.resize_mode in ["right", "corner"]:
            new_width = max(300, current_size.width() + diff.x())

        if self.resize_mode in ["bottom", "corner"]:
            new_height = max(150, current_size.height() + diff.y())

        # Create ghost overlay for smooth resize feedback if it doesn't exist
        if not self.resize_ghost and (abs(diff.x()) > 5 or abs(diff.y()) > 5):
            self.resize_ghost = QWidget(None)
            self.resize_ghost.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.resize_ghost.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.resize_ghost.setStyleSheet("background-color: rgba(137, 180, 250, 0.2); border: 1px solid #89b4fa;")
            self.resize_ghost.show()

        # Update ghost position and size
        if self.resize_ghost:
            self.resize_ghost.setGeometry(self.x(), self.y(), new_width, new_height)

        # Actually resize window at a reduced rate for performance
        # This avoids lag during rapid resizing
        if not hasattr(self, 'last_resize_time') or time.time() - self.last_resize_time > 0.05:
            self.resize(new_width, new_height)
            self.last_resize_time = time.time()

        self.drag_start_position = global_pos
        self.update_status(f"Resizing...")

    def mouseReleaseEvent(self, event):
        # Apply final size when mouse released and clean up ghost
        if self.resize_mode and self.resize_ghost:
            # Get final size from ghost
            final_size = self.resize_ghost.size()
            self.resize(final_size.width(), final_size.height())

            # Clean up ghost
            self.resize_ghost.close()
            self.resize_ghost.deleteLater()
            self.resize_ghost = None

            self.update_status(f"Resized to {final_size.width()}x{final_size.height()}")

        self.drag_start_position = None
        self.resize_mode = None

    def showEvent(self, event):
        # Update main frame rounded corners on show
        self.main_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        super().showEvent(event)

class SettingsDialog(QDialog):
    """Settings dialog for model selection"""

    def __init__(self, current_model, parent=None):
        super().__init__(parent)
        self.current_model = current_model
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 400)  # Reduced from 500x400 to 400x320
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        self.setup_ui()
        self.center_on_screen()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced from 25px to 20px
        layout.setSpacing(15)  # Reduced from 20px to 15px

        # Header
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("""
            QLabel {
                color: #89b4fa;
                font: bold 18px 'Segoe UI';  /* Reduced from 20px to 18px */
            }
        """)

        subtitle = QLabel("Configure your AI model and preferences")
        subtitle.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                margin-top: 3px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Add some vertical spacing
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setStyleSheet("""
            QFrame {
                color: #45475a;
                background-color: #45475a;
                border: none;
                max-height: 1px;
                margin-top: 3px;
                margin-bottom: 3px;
            }
        """)
        layout.addWidget(spacer)

        # Model selection
        model_label = QLabel("🤖 Ollama Model:")
        model_label.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: bold 13px 'Segoe UI';  /* Reduced from 14px to 13px */
                margin-top: 5px;  /* Reduced from 8px to 5px */
            }
        """)

        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText(self.current_model)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #45475a;
                color: #cdd6f4;
                font: 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                padding: 6px;  /* Reduced from 8px to 6px */
                border: none;
                border-radius: 5px;
                min-height: 28px;  /* Reduced from 30px to 28px */
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;  /* Reduced from 30px to 25px */
            }
            QComboBox::down-arrow {
                color: #cdd6f4;
                width: 20px;  /* Added width */
                height: 20px;  /* Added height */
            }
            QComboBox QAbstractItemView {
                background-color: #45475a;
                color: #cdd6f4;
                font: 15px 'Segoe UI';
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                padding: 8px;
                border: none;
            }
        """)

        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)

        # Status section
        status_label = QLabel("📊 Connection Status:")
        status_label.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: bold 13px 'Segoe UI';  /* Reduced from 14px to 13px */
                margin-top: 5px;  /* Reduced from 8px to 5px */
            }
        """)

        self.status_text = QLabel("Checking Ollama status...")
        self.status_text.setStyleSheet("""
            QLabel {
                background-color: #45475a;
                color: #cdd6f4;
                font: 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                padding: 10px;  /* Reduced from 12px to 10px */
                border-radius: 5px;
                min-height: 50px;  /* Reduced from 60px to 50px */
            }
        """)
        self.status_text.setWordWrap(True)

        layout.addWidget(status_label)
        layout.addWidget(self.status_text)

        # Check Ollama status
        self.check_ollama_status()

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self.get_button_style("#313244", "#45475a"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)

        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet(self.get_button_style("#89b4fa", "#74c7ec", True))
        save_btn.clicked.connect(self.accept)
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(150)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

    def get_button_style(self, bg_color, hover_color, primary=False):
        text_color = "#1e1e2e" if primary else "#cdd6f4"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font: {'bold' if primary else 'normal'} 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                padding: 8px 20px;  /* Reduced from 10px/24px to 8px/20px */
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    def check_ollama_status(self):
        try:
            models = ollama.list().get('models', [])
            status_text = f"✅ Connected successfully!\nFound {len(models)} available models."
            self.status_text.setStyleSheet("""
                QLabel {
                    background-color: #45475a;
                    color: #a6e3a1;
                    font: 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                    padding: 10px;  /* Reduced from 12px to 10px */
                    border-radius: 5px;
                    min-height: 50px;  /* Reduced from 60px to 50px */
                }
            """)
        except Exception as e:
            status_text = f"❌ Connection failed\n{str(e)[:80]}...\n\nPlease ensure Ollama is installed and running."
            self.status_text.setStyleSheet("""
                QLabel {
                    background-color: #45475a;
                    color: #f38ba8;
                    font: 12px 'Segoe UI';  /* Reduced from 13px to 12px */
                    padding: 10px;  /* Reduced from 12px to 10px */
                    border-radius: 5px;
                    min-height: 50px;  /* Reduced from 60px to 50px */
                }
            """)

        self.status_text.setText(status_text)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def get_selected_model(self):
        return self.model_combo.currentText()

class ControlWindow(QMainWindow):
    """Main control window"""

    def __init__(self):
        super().__init__()
        self.current_model = AVAILABLE_MODELS[0]
        self.translation_overlay = None
        self.screen_selector = None
        self.translation_worker = None

        self.setup_ui()
        self.center_on_screen()

        # Initialize Tesseract
        self._initialize_tesseract()

        # Setup keyboard hook
        self.last_alt_press_time = 0
        keyboard.on_press(self._on_alt_pressed)

    def setup_ui(self):
        self.setWindowTitle("Screen Translator")
        self.setFixedSize(300, 350)  # Increased window size

        # Set modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header
        self.setup_header(layout)

        # Buttons
        self.setup_buttons(layout)

        # Footer
        self.setup_footer(layout)

    def setup_header(self, layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title = QLabel("Screen Translator")
        title.setStyleSheet("""
            QLabel {
                color: #89b4fa;
                font: bold 20px 'Segoe UI';
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("OCR • Translation • AI")
        subtitle.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: 13px 'Segoe UI';
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

    def setup_buttons(self, layout):
        # Capture button
        capture_btn = QPushButton("📱 Capture Screen Area")
        capture_btn.setStyleSheet(self.get_button_style())
        capture_btn.clicked.connect(self.start_screen_selection)
        capture_btn.setMinimumHeight(45)  # Taller button

        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(self.get_button_style())
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setMinimumHeight(45)  # Taller button

        layout.addWidget(capture_btn)
        layout.addWidget(settings_btn)

    def setup_footer(self, layout):
        # Info
        info_label = QLabel("💡 Press Alt twice quickly to capture")
        info_label.setStyleSheet("""
            QLabel {
                color: #6c7086;
                font: 12px 'Segoe UI';
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Separator
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

        # Version
        version_label = QLabel("v1.0 • AI-Powered Translation")
        version_label.setStyleSheet("""
            QLabel {
                color: #6c7086;
                font: 11px 'Segoe UI';
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(info_label)
        layout.addWidget(separator)
        layout.addWidget(version_label)

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                font: 14px 'Segoe UI';
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #ffffff;
            }
        """

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _initialize_tesseract(self):
        """Initialize Tesseract OCR"""
        if os.path.exists(TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        else:
            QMessageBox.warning(self, "Tesseract OCR Missing",
                              "Tesseract OCR not found. Please install it and configure the TESSERACT_PATH.")

    def start_screen_selection(self):
        """Start screen area selection"""
        # Close any existing screen selector
        if hasattr(self, 'screen_selector') and self.screen_selector:
            try:
                self.screen_selector.close()
                self.screen_selector.deleteLater()
            except Exception as e:
                print(f"Error closing screen selector: {e}")

        # Create a new screen selector
        self.screen_selector = None  # Clear reference first
        QApplication.processEvents()  # Process pending events

        # Create new selector and connect the signal
        self.screen_selector = ScreenSelector()
        self.screen_selector.area_selected.connect(self.process_selected_area)

        # Use single-shot timer to ensure proper event processing and display
        QTimer.singleShot(100, self._show_screen_selector)

    def _show_screen_selector(self):
        """Show screen selector with proper timing"""
        if self.screen_selector:
            # Show the selector on top of everything
            self.screen_selector.show()
            self.screen_selector.raise_()
            self.screen_selector.activateWindow()

            # Ensure it's visible and on top
            QTimer.singleShot(50, self.screen_selector.ensure_visibility)

    def process_selected_area(self, x, y, width, height):
        """Process the selected screen area"""
        print(f"Selected area: x={x}, y={y}, width={width}, height={height}")

        # Create translation overlay if it doesn't exist
        if not self.translation_overlay:
            self.translation_overlay = TranslationOverlay()
            self.translation_overlay.show()

        self.translation_overlay.update_text("กำลังสกัดข้อความจากภาพ...")

        # Add a longer delay before capturing to ensure the selection window is fully closed
        QTimer.singleShot(300, lambda: self.capture_and_process(x, y, width, height))

    def capture_and_process(self, x, y, width, height):
        """Capture and process the selected area"""
        try:
            # Process any pending events before capture
            QApplication.processEvents()

            # Capture text from screen
            captured_text = self.get_text_from_screen_area(x, y, width, height)
            print(f"[INFO] Captured Text: '{captured_text}'")

            if captured_text and not captured_text.startswith("ERROR:"):
                self.translation_overlay.update_text("กำลังแปล...")

                # Start translation in background thread
                self.translation_worker = TranslationWorker(captured_text, self.current_model)
                self.translation_worker.translation_finished.connect(self.on_translation_finished)
                self.translation_worker.start()
            else:
                error_msg = captured_text if captured_text.startswith("ERROR:") else "ไม่พบข้อความที่จะแปล หรือการดึงข้อความล้มเหลว"
                self.translation_overlay.update_text(error_msg)
        except Exception as e:
            print(f"Error in capture_and_process: {e}")
            if self.translation_overlay:
                self.translation_overlay.update_text(f"เกิดข้อผิดพลาด: {str(e)}")

    def get_text_from_screen_area(self, x, y, width, height):
        """Capture text from screen area using OCR"""
        try:
            with mss.mss() as sct:
                # Ensure coordinates and dimensions are positive integers
                x, y = max(0, int(x)), max(0, int(y))
                width, height = max(1, int(width)), max(1, int(height))

                # Define the capture area
                monitor = {"top": y, "left": x, "width": width, "height": height}

                # Capture the screen area
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # Convert to grayscale to improve OCR
                img = img.convert('L')

                # Use Tesseract OCR to extract text
                text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')

                # If text is empty, try different OCR settings
                if not text.strip():
                    text = pytesseract.image_to_string(img, lang='eng', config='--psm 3')

                return text.strip()

        except pytesseract.pytesseract.TesseractNotFoundError:
            return "ERROR: Tesseract OCR not installed or not in PATH"
        except Exception as e:
            print(f"[ERROR] Screen capture exception: {e}")
            return f"ERROR: {str(e)}"

    def on_translation_finished(self, translated_text):
        """Handle translation completion"""
        if self.translation_overlay:
            self.translation_overlay.update_text(translated_text)
        print(f"[INFO] Translated Text: '{translated_text}'")

    @staticmethod
    def _get_text_from_screen_area(x, y, width, height):
        """Capture text from screen area using OCR"""
        try:
            # Ensure we're not trying to capture while another operation is in progress
            QApplication.processEvents()

            with mss.mss() as sct:
                # Ensure coordinates and dimensions are positive integers
                x, y = max(0, int(x)), max(0, int(y))
                width, height = max(1, int(width)), max(1, int(height))

                # Capture the screen area
                monitor = {"top": y, "left": x, "width": width, "height": height}
                sct_img = sct.grab(monitor)

                # Convert to PIL Image for OCR processing
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

                # Apply some image processing to improve OCR accuracy
                img = img.convert('L')  # Convert to grayscale

                # Perform OCR
                text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')

                # If text is empty, try different OCR settings
                if not text.strip():
                    text = pytesseract.image_to_string(img, lang='eng', config='--psm 3')

                return text.strip()
        except pytesseract.pytesseract.TesseractNotFoundError:
            return "ERROR: Tesseract OCR not installed or not in PATH"
        except Exception as e:
            print(f"[ERROR] Screen capture exception: {e}")
            return f"ERROR: {str(e)}"

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.current_model, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_model = dialog.get_selected_model()
            print(f"[INFO] Changed model to: {self.current_model}")

    def _on_alt_pressed(self, e):
        """Handle Alt key double press"""
        if e.event_type == keyboard.KEY_DOWN and e.name == 'alt':
            current_time = time.time()
            if 0.1 < (current_time - self.last_alt_press_time) < ALT_DOUBLE_PRESS_THRESHOLD:
                print("\n[INFO] Double Alt detected! Starting screen selection...")
                # Use QTimer to call from main thread with sufficient delay
                QTimer.singleShot(100, self.start_screen_selection)
            self.last_alt_press_time = current_time

    def closeEvent(self, event):
        """Handle application closing"""
        try:
            keyboard.unhook_all()
        except Exception as e:
            print(f"Could not unhook keyboard: {e}")

        if self.translation_overlay:
            self.translation_overlay.close()

        event.accept()

class ScreenTranslatorApp:
    """Main application class"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')  # Use Fusion style for better appearance

        # Apply modern dark palette to entire application
        self.apply_dark_palette()

        # Set application properties
        self.app.setApplicationName("Screen Translator")
        self.app.setApplicationVersion("1.0")

        # Check initial dependencies
        self._check_dependencies()

        # Create main window
        self.main_window = ControlWindow()

    def apply_dark_palette(self):
        """Apply dark palette to entire application"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 46))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(205, 214, 244))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(49, 50, 68))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 46))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 46))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(205, 214, 244))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(205, 214, 244))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(49, 50, 68))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(205, 214, 244))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(137, 180, 250))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(137, 180, 250))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(30, 30, 46))
        self.app.setPalette(dark_palette)

    def _check_dependencies(self):
        """Check for required dependencies"""
        if not os.path.exists(TESSERACT_PATH):
            QMessageBox.warning(None, "Tesseract OCR Missing",
                              "Tesseract OCR not found. Please install it and configure the TESSERACT_PATH.")

        try:
            ollama.list()
        except Exception as e:
            QMessageBox.warning(None, "Ollama Connection Issue",
                              f"Could not connect to Ollama: {e}\nPlease ensure it is installed and running.")

    def run(self):
        """Run the application"""
        print("Screen Translator Program Started.")
        print("Press Alt twice quickly to select screen area.")

        self.main_window.show()
        return self.app.exec()

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    sys.exit(app.run())