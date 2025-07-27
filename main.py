# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

import sys
from src.core.app import ScreenTranslatorApp

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    sys.exit(app.run())