import os
import json
import shutil
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint, QSize, QRect

class Config:
    """Application configuration"""
    
    @staticmethod
    def dpi_scale(value):
        """Scale a value based on the current screen's DPI
        
        This helps ensure UI elements have consistent physical size
        regardless of screen DPI/scaling settings.
        """
        if not QApplication.instance():
            return value  # Return original value if QApplication not initialized
            
        # Get the primary screen's device pixel ratio
        screen = QApplication.primaryScreen()
        if not screen:
            return value
            
        ratio = screen.devicePixelRatio()
        return int(value * ratio)
        
    @staticmethod
    def dpi_point(x, y):
        """Create a DPI-aware QPoint"""
        return QPoint(Config.dpi_scale(x), Config.dpi_scale(y))
        
    @staticmethod
    def dpi_size(width, height):
        """Create a DPI-aware QSize"""
        return QSize(Config.dpi_scale(width), Config.dpi_scale(height))
        
    @staticmethod
    def dpi_rect(x, y, width, height):
        """Create a DPI-aware QRect"""
        return QRect(
            Config.dpi_scale(x), 
            Config.dpi_scale(y), 
            Config.dpi_scale(width), 
            Config.dpi_scale(height)
        )
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

# Initialize Config.TESSERACT_PATH after class definition
Config.TESSERACT_PATH = Config.get_tesseract_path()