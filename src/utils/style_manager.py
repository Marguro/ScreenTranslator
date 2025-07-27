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