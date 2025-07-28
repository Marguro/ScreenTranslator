import pyperclip
from PyQt6.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QTextEdit, QDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve

from src.config import Config
from src.utils import StyleManager
from src.ui import StatusIndicator, CopyIndicator

# Use lazy imports to avoid circular dependencies
def get_settings_dialog():
    from src.ui.settings_dialog import SettingsDialog
    return SettingsDialog

def get_control_window():
    from src.ui.control_window import ControlWindow
    return ControlWindow

class TranslationOverlay(QWidget):
    """Modern floating translation window"""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_variables()
        self.setup_ui()
        self._setup_animations()
        
        # Install event filter on self to handle events from child widgets
        self.installEventFilter(self)

    def _setup_window(self):
        """Configure window properties"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Enable mouse tracking to receive mouse move events even when not pressed
        self.setMouseTracking(True)

        # Position near top-right corner
        screen = QApplication.primaryScreen().geometry()
        # Use DPI-aware sizing
        self.resize(Config.dpi_scale(Config.OVERLAY_WIDTH), Config.dpi_scale(Config.OVERLAY_HEIGHT))
        # Use DPI-aware positioning
        self.move(screen.width() - Config.dpi_scale(Config.OVERLAY_WIDTH + 20), Config.dpi_scale(50))
        
    def _enable_mouse_tracking_for_children(self, widget):
        """Recursively enable mouse tracking for all child widgets"""
        widget.setMouseTracking(True)
        
        # Process all child widgets recursively
        for child in widget.findChildren(QWidget, options=Qt.FindChildOption.FindChildrenRecursively):
            child.setMouseTracking(True)
            # Install event filter on all child widgets
            child.installEventFilter(self)
            
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        # Enable mouse tracking for all child widgets when shown
        self._enable_mouse_tracking_for_children(self)
        
    def eventFilter(self, watched, event):
        """Filter events from child widgets"""
        if event.type() == event.Type.MouseMove:
            # Update cursor based on global position
            local_pos = self.mapFromGlobal(event.globalPosition().toPoint())
            self._update_cursor(local_pos)
            
        # Always return False to allow the event to be processed further
        return False

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
        self.resize_margin = Config.dpi_scale(15)  # DPI-aware resize margin

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet(StyleManager.get_overlay_style())
        self.main_frame.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)

        # Inner layout with DPI-aware margins and spacing
        inner_layout = QVBoxLayout(self.main_frame)
        inner_layout.setContentsMargins(
            Config.dpi_scale(20), 
            Config.dpi_scale(15), 
            Config.dpi_scale(20), 
            Config.dpi_scale(15)
        )
        inner_layout.setSpacing(Config.dpi_scale(12))

        # Setup sections
        self._setup_header(inner_layout)
        self._setup_content(inner_layout)
        self._setup_footer(inner_layout)

    def _setup_header(self, layout):
        """Setup header with title and controls"""
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.header_frame.setFixedHeight(Config.dpi_scale(40))
        self.header_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header_frame.setMouseTracking(True)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(Config.dpi_scale(10))

        # Title section
        title_layout = QHBoxLayout()
        title_layout.setSpacing(Config.dpi_scale(8))

        icon_label = QLabel("🌐")
        icon_label.setStyleSheet(f"font-size: {Config.dpi_scale(18)}px; color: #89b4fa;")

        # Store reference to title label for easy updates
        self.title_label = QLabel("Translation")
        self.title_label.setStyleSheet(f"color: #cdd6f4; font: bold {Config.dpi_scale(14)}px 'Segoe UI';")

        drag_hint = QLabel("• • •")
        drag_hint.setStyleSheet(f"color: rgba(205, 214, 244, 0.5); font: bold {Config.dpi_scale(12)}px 'Segoe UI';")

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
        self.translation_text.setMinimumHeight(Config.dpi_scale(60))
        self.translation_text.setMaximumHeight(Config.dpi_scale(1500))
        self.translation_text.setMouseTracking(True)
        layout.addWidget(self.translation_text)

    def _setup_footer(self, layout):
        """Setup footer with status indicators"""
        self.footer_frame = QFrame()
        self.footer_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.footer_frame.setFixedHeight(Config.dpi_scale(30))
        self.footer_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.footer_frame.setMouseTracking(True)

        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(Config.dpi_scale(10))

        # Status and copy indicators
        self.status_indicator = StatusIndicator()
        self.copy_indicator = CopyIndicator()

        footer_layout.addWidget(self.status_indicator)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_indicator)
        layout.addWidget(self.footer_frame)

    def _setup_animations(self):
        """Setup entrance animations"""
        # Start by hiding the widget
        self.setWindowOpacity(0.0)

        # Store the original position
        self.original_pos = self.pos()

        # Set initial position for slide animation with DPI-aware offset
        start_pos = QPoint(self.original_pos.x(), self.original_pos.y() - Config.dpi_scale(30))
        self.move(start_pos)

        # Fade-in animation (using window opacity instead of graphics effect)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)  # Duration in ms doesn't need DPI scaling
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide-in animation
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(400)  # Duration in ms doesn't need DPI scaling
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(self.original_pos)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Scale animation for "pop-in" effect
        self.scale_animation = QPropertyAnimation(self, b"size")
        self.scale_animation.setDuration(400)  # Duration in ms doesn't need DPI scaling

        # Start slightly smaller
        start_size = QSize(int(self.width() * 0.95), int(self.height() * 0.95))
        end_size = self.size()

        self.scale_animation.setStartValue(start_size)
        self.scale_animation.setEndValue(end_size)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)

        # Start all animations together
        QTimer.singleShot(50, self._start_animations)

    def _start_animations(self):
        """Start all animations"""
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
        ControlWindow = get_control_window()
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ControlWindow):
                main_window = widget
                break

        if main_window:
            # Create and show settings dialog
            SettingsDialog = get_settings_dialog()
            dialog = SettingsDialog(main_window.current_model, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_display_name = dialog.get_selected_model()
                main_window.current_model = Config.AVAILABLE_MODELS[selected_display_name]
                main_window._update_model_status()  # Update the model status display

                # Update the overlay header immediately
                self._update_model_display(main_window.current_model)
        else:
            # Fallback if main window not found
            SettingsDialog = get_settings_dialog()
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

    def _update_cursor(self, pos):
        """Update cursor shape based on position"""
        resize_edge = self._get_resize_edge(pos)
        
        if resize_edge == "top-left" or resize_edge == "bottom-right":
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif resize_edge == "top-right" or resize_edge == "bottom-left":
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif resize_edge == "top" or resize_edge == "bottom":
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif resize_edge == "left" or resize_edge == "right":
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and resizing"""
        # Always update cursor based on position
        self._update_cursor(event.position().toPoint())
        
        # Handle resizing and dragging
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

        # Apply size constraints with DPI awareness
        min_width = Config.dpi_scale(500)
        min_height = Config.dpi_scale(150)
        max_width = Config.dpi_scale(1200)
        max_height = Config.dpi_scale(1500)

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