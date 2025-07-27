from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QRubberBand
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QPainter, QPen, QRegion

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