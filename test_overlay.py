import sys
from PyQt6.QtWidgets import QApplication
from src.ui.translation_overlay import TranslationOverlay

def main():
    app = QApplication(sys.argv)
    overlay = TranslationOverlay()
    overlay.show()
    overlay.update_text("This is a test overlay window.\nMove your cursor to the edges and corners to see the cursor change.\nThis indicates that the window can be resized.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()