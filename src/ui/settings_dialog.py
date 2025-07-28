from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from src.config import Config
from src.utils import StyleManager

# Use lazy imports to avoid circular dependencies
def get_translation_overlay():
    from src.ui.translation_overlay import TranslationOverlay
    return TranslationOverlay

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

        # Create a container for the font size dropdown
        font_display_container = QHBoxLayout()
        font_display_container.setSpacing(8)

        # Create font size dropdown
        self.font_size_combo = QComboBox()
        self.font_size_combo.setStyleSheet("""
            QComboBox {
                background-color: #45475a;
                color: #cdd6f4;
                font: 12px 'Segoe UI';
                padding: 8px;
                border: none;
                border-radius: 5px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                padding: 8px;
            }
        """)
        
        # Add font sizes from Config
        for size in Config.FONT_SIZES:
            self.font_size_combo.addItem(f"{size} px", size)
            
        # Find and select the current font size
        current_size_index = 0
        for i in range(self.font_size_combo.count()):
            if self.font_size_combo.itemData(i) == Config.DEFAULT_FONT_SIZE:
                current_size_index = i
                break
        self.font_size_combo.setCurrentIndex(current_size_index)
        
        # Connect signal
        # noinspection PyUnresolvedReferences
        self.font_size_combo.currentIndexChanged.connect(self._font_size_changed)
        
        # Store current font size
        self.current_font_size = Config.DEFAULT_FONT_SIZE
        
        # Add font size dropdown to the display container
        font_display_container.addWidget(self.font_size_combo)
        
        # Add the display container to the main layout
        font_controls_layout.addLayout(font_display_container)

        layout.addWidget(font_label)
        layout.addLayout(font_controls_layout)

    def _font_size_changed(self, index):
        """Handle font size selection from dropdown"""
        self.current_font_size = self.font_size_combo.itemData(index)

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
        from PyQt6.QtWidgets import QApplication
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
            from PyQt6.QtWidgets import QApplication
            TranslationOverlay = get_translation_overlay()
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