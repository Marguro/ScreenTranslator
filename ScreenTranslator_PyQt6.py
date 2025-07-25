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

# Model mapping: Display Name -> Actual Model Name
AVAILABLE_MODELS = {
    "Gemma 3n (Unsloth)": "hf.co/unsloth/gemma-3n-E4B-it-GGUF:Q4_K_XL",
    "Gemma 3n": "gemma3n"
}

# Model-specific configurations
def get_model_options(model_name):
    """Get specific options for each model"""
    # Unsloth recommended settings
    if "unsloth" in model_name.lower() or "hf.co/unsloth" in model_name:
        return {
            'temperature': 1.0,
            'top_k': 64,
            'top_p': 0.95,
            'min_p': 0.0,
            'num_predict': 200
        }
    # Default settings for other models
    else:
        return {
            'temperature': 0.1,
            'num_predict': 200
        }

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

            # Get model-specific options
            model_options = get_model_options(self.model)

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options=model_options
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
    """Modern floating translation window"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Window properties
        self.resize(500, 200)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 520, 50)  # Position near top-right corner

        # Drag variables
        self.drag_start_position = None
        self.is_dragging = False

        # Resize variables
        self.resize_start_position = None
        self.resize_start_geometry = None
        self.is_resizing = False
        self.resize_edge = None
        self.resize_margin = 8  # Resize detection margin

        self.setup_ui()

    def setup_ui(self):
        # Main container with modern glassmorphism design
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(45, 45, 68, 0.95), 
                    stop:1 rgba(30, 30, 46, 0.95));
                border: 1px solid rgba(137, 180, 250, 0.3);
                border-radius: 15px;
            }
        """)

        # Add glow effect
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setBlurRadius(20)  # Reduced from 30
        glow_effect.setColor(QColor(137, 180, 250, 40))  # Reduced opacity
        glow_effect.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(glow_effect)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)

        # Inner layout
        inner_layout = QVBoxLayout(self.main_frame)
        inner_layout.setContentsMargins(20, 15, 20, 15)
        inner_layout.setSpacing(12)

        # Header with title and close button
        self.setup_header(inner_layout)

        # Content area
        self.setup_content(inner_layout)

        # Footer with status
        self.setup_footer(inner_layout)

    def setup_header(self, layout):
        # Create draggable header
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Icon and title
        icon_title_layout = QHBoxLayout()
        icon_title_layout.setSpacing(8)

        # Translation icon
        icon_label = QLabel("🌐")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #89b4fa;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

        # Title
        title = QLabel("Translation")
        title.setStyleSheet("""
            QLabel {
                color: #cdd6f4;
                font: bold 14px 'Segoe UI';
                background: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        # Drag hint
        drag_hint = QLabel("• • •")
        drag_hint.setStyleSheet("""
            QLabel {
                color: rgba(205, 214, 244, 0.5);
                font: bold 12px 'Segoe UI';
                background: transparent;
                border: none;
                padding: 0px 5px;
            }
        """)

        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title)
        icon_title_layout.addWidget(drag_hint)

        header_layout.addLayout(icon_title_layout)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(243, 139, 168, 0.1);
                color: #f38ba8;
                border: 1px solid rgba(243, 139, 168, 0.3);
                border-radius: 12px;
                font: bold 12px 'Segoe UI';
                padding: 4px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background: rgba(243, 139, 168, 0.2);
                border: 1px solid rgba(243, 139, 168, 0.5);
            }
            QPushButton:pressed {
                background: rgba(243, 139, 168, 0.3);
            }
        """)
        close_btn.clicked.connect(self.close)

        header_layout.addWidget(close_btn)
        layout.addWidget(self.header_frame)

    def setup_content(self, layout):
        # Translation text area
        self.translation_text = QTextEdit()
        self.translation_text.setStyleSheet("""
            QTextEdit {
                background: rgba(49, 50, 68, 0.6);
                color: #cdd6f4;
                font: 13px 'Segoe UI';
                border: 1px solid rgba(137, 180, 250, 0.2);
                border-radius: 10px;
                padding: 12px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QTextEdit:focus {
                border: 1px solid rgba(137, 180, 250, 0.4);
            }
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
        """)
        self.translation_text.setReadOnly(True)
        # Set initial size constraints
        self.translation_text.setMinimumHeight(60)
        self.translation_text.setMaximumHeight(300)  # Increased maximum to allow more text

        layout.addWidget(self.translation_text)

    def setup_footer(self, layout):
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #a6e3a1;
                font: 11px 'Segoe UI';
                background: rgba(166, 227, 161, 0.1);
                border: 1px solid rgba(166, 227, 161, 0.3);
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)

        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()

        # Copy indicator (shows when text is copied)
        self.copy_indicator = QLabel("📋 Copied!")
        self.copy_indicator.setStyleSheet("""
            QLabel {
                color: #89b4fa;
                font: 11px 'Segoe UI';
                background: rgba(137, 180, 250, 0.1);
                border: 1px solid rgba(137, 180, 250, 0.3);
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)
        self.copy_indicator.hide()

        footer_layout.addWidget(self.copy_indicator)
        layout.addLayout(footer_layout)

    def update_text(self, text):
        """Update translation text and copy to clipboard"""
        self.translation_text.setPlainText(text)
        pyperclip.copy(text)

        # Show copy indicator briefly
        self.copy_indicator.show()
        QTimer.singleShot(2000, self.copy_indicator.hide)

        # Update status based on content
        if text.startswith("กำลัง"):
            self.update_status("Processing...", "#fab387")
        elif text.startswith("Translation Error"):
            self.update_status("Error", "#f38ba8")
        else:
            self.update_status("Completed", "#a6e3a1")

    def update_status(self, status, color="#a6e3a1"):
        """Update status with color"""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font: 11px 'Segoe UI';
                background: rgba({self.hex_to_rgba(color, 0.1)});
                border: 1px solid rgba({self.hex_to_rgba(color, 0.3)});
                border-radius: 8px;
                padding: 4px 8px;
            }}
        """)

    def hex_to_rgba(self, hex_color, alpha):
        """Convert hex color to rgba string"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha}"

    def showEvent(self, event):
        """Animate entrance"""
        super().showEvent(event)

        # Fade in animation
        self.setWindowOpacity(0)
        self.fade_animation = QTimer()
        self.fade_animation.timeout.connect(self.fade_in)
        self.fade_animation.start(16)  # ~60 FPS
        self.fade_value = 0

    def fade_in(self):
        """Smooth fade in effect"""
        self.fade_value += 0.1
        if self.fade_value >= 1.0:
            self.fade_value = 1.0
            self.fade_animation.stop()
        self.setWindowOpacity(self.fade_value)

    def closeEvent(self, event):
        """Animate exit"""
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        event.accept()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.MouseButton.LeftButton:
            click_pos = event.position().toPoint()

            # Check for resize edge first
            resize_edge = self.get_resize_edge(click_pos)
            if resize_edge:
                self.is_resizing = True
                self.resize_edge = resize_edge
                self.resize_start_position = event.globalPosition().toPoint()
                self.resize_start_geometry = self.geometry()
                # Don't change cursor during resize
                return

            # Check if click is on header frame for dragging
            header_rect = self.header_frame.geometry()
            if header_rect.contains(click_pos):
                self.is_dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.pos()
                # Don't change cursor during drag
                # self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and resizing"""
        if self.is_resizing:
            self.perform_resize(event.globalPosition().toPoint())
        elif self.is_dragging and self.drag_start_position is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            self.move(new_pos)
        # Remove cursor updates during mouse move
        # else:
        #     # Update cursor based on position
        #     self.update_cursor_for_resize(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.drag_start_position = None
            self.resize_start_position = None
            self.resize_start_geometry = None
            self.resize_edge = None

            # Don't update cursor after release
            # self.update_cursor_for_resize(event.position().toPoint())

    def get_resize_edge(self, pos):
        """Determine which edge/corner is being clicked for resizing"""
        rect = self.rect()
        margin = self.resize_margin

        # Check corners first (they take priority over edges)
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

    def perform_resize(self, global_pos):
        """Perform the actual resizing based on the edge being dragged"""
        if not self.is_resizing or not self.resize_edge:
            return

        # Calculate the difference from start position
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

        # Calculate fixed heights for header and footer
        header_height = self.header_frame.height() + 15  # Include spacing
        footer_height = 60  # Approximate footer height with spacing
        fixed_height = header_height + footer_height + 40  # Add margins

        # Set minimum and maximum constraints
        min_width = 300
        min_text_height = 60  # Minimum height for text area
        max_text_height = 600  # Maximum height for text area
        min_height = fixed_height + min_text_height
        max_height = fixed_height + max_text_height

        # Apply width constraints
        if new_width < min_width:
            if "left" in self.resize_edge:
                new_x = new_x - (min_width - new_width)
            new_width = min_width

        # Apply height constraints
        if new_height < min_height:
            if "top" in self.resize_edge:
                new_y = new_y - (min_height - new_height)
            new_height = min_height
        elif new_height > max_height:
            if "top" in self.resize_edge:
                new_y = new_y + (new_height - max_height)
            new_height = max_height

        # Apply the new geometry
        self.setGeometry(new_x, new_y, new_width, new_height)

        # Update the text area height based on new window size
        self.update_text_area_height()

    def update_text_area_height(self):
        """Update the height of the text area based on the current window size"""
        # Calculate available height for text area
        total_height = self.height()
        header_height = self.header_frame.height() + 15  # Include spacing
        footer_height = 60  # Footer height with spacing
        margins = 40  # Total margins

        # Calculate new text area height
        available_height = total_height - header_height - footer_height - margins

        # Ensure it stays within reasonable bounds
        text_height = max(60, min(available_height, 600))

        # Update the text area size
        self.translation_text.setMinimumHeight(text_height)
        self.translation_text.setMaximumHeight(text_height)

        # Force layout update
        self.main_frame.layout().update()

    # Comment out the cursor update method to disable cursor changes
    # def update_cursor_for_resize(self, pos):
    #     """Update cursor based on position for resize indication"""
    #     edge = self.get_resize_edge(pos)
    #
    #     if edge in ["top-left", "bottom-right"]:
    #         self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
    #     elif edge in ["top-right", "bottom-left"]:
    #         self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
    #     elif edge in ["left", "right"]:
    #         self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
    #     elif edge in ["top", "bottom"]:
    #         self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
    #     elif self.header_frame.geometry().contains(pos):
    #         self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
    #     else:
    #         self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def perform_resize(self, global_pos):
        """Perform the actual resizing based on the edge being dragged"""
        if not self.is_resizing or not self.resize_edge:
            return

        # Calculate the difference from start position
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

        # Calculate fixed heights for header and footer
        header_height = self.header_frame.height() + 15  # Include spacing
        footer_height = 60  # Approximate footer height with spacing
        fixed_height = header_height + footer_height + 40  # Add margins

        # Set minimum and maximum constraints
        min_width = 300
        min_text_height = 60  # Minimum height for text area
        max_text_height = 600  # Maximum height for text area
        min_height = fixed_height + min_text_height
        max_height = fixed_height + max_text_height

        # Apply width constraints
        if new_width < min_width:
            if "left" in self.resize_edge:
                new_x = new_x - (min_width - new_width)
            new_width = min_width

        # Apply height constraints
        if new_height < min_height:
            if "top" in self.resize_edge:
                new_y = new_y - (min_height - new_height)
            new_height = min_height
        elif new_height > max_height:
            if "top" in self.resize_edge:
                new_y = new_y + (new_height - max_height)
            new_height = max_height

        # Apply the new geometry
        self.setGeometry(new_x, new_y, new_width, new_height)

        # Update the text area height based on new window size
        self.update_text_area_height()

    def update_text_area_height(self):
        """Update the height of the text area based on the current window size"""
        # Calculate available height for text area
        total_height = self.height()
        header_height = self.header_frame.height() + 15  # Include spacing
        footer_height = 60  # Footer height with spacing
        margins = 40  # Total margins

        # Calculate new text area height
        available_height = total_height - header_height - footer_height - margins

        # Ensure it stays within reasonable bounds
        text_height = max(60, min(available_height, 600))

        # Update the text area size
        self.translation_text.setMinimumHeight(text_height)
        self.translation_text.setMaximumHeight(text_height)

        # Force layout update
        self.main_frame.layout().update()

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
        self.model_combo.addItems(AVAILABLE_MODELS.keys())

        # Find the display name for the current model
        current_display_name = None
        for display_name, actual_name in AVAILABLE_MODELS.items():
            if actual_name == self.current_model:
                current_display_name = display_name
                break

        if current_display_name:
            self.model_combo.setCurrentText(current_display_name)
        else:
            self.model_combo.setCurrentIndex(0)

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
        self.current_model = list(AVAILABLE_MODELS.values())[0]
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

        # Create or recreate translation overlay (handle case where it was closed)
        if not self.translation_overlay or not self.translation_overlay.isVisible():
            if self.translation_overlay:
                # Clean up existing overlay if it exists but is not visible
                self.translation_overlay.close()
                self.translation_overlay.deleteLater()

            self.translation_overlay = TranslationOverlay()
            self.translation_overlay.show()
        else:
            # If overlay exists and is visible, just bring it to front
            self.translation_overlay.show()
            self.translation_overlay.raise_()
            self.translation_overlay.activateWindow()

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
            selected_display_name = dialog.get_selected_model()
            # Convert display name to actual model name
            self.current_model = AVAILABLE_MODELS[selected_display_name]
            print(f"[INFO] Changed model to: {selected_display_name} ({self.current_model})")

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