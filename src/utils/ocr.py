import os
import mss
from PIL import Image
import pytesseract
from PyQt6.QtWidgets import QApplication
from src.config import Config

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
                # Convert coordinates from device-independent pixels to physical screen pixels
                # This is necessary when the screen scaling is not 100%
                if QApplication.instance():
                    screen = QApplication.primaryScreen()
                    if screen:
                        # Get the device pixel ratio (e.g., 1.5 for 150% scaling)
                        ratio = screen.devicePixelRatio()
                        if ratio != 1.0:
                            # Convert coordinates to physical pixels
                            x, y = int(x * ratio), int(y * ratio)
                            width, height = int(width * ratio), int(height * ratio)
                
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