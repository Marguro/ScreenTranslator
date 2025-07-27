@echo off
echo Building Screen Translator Executable...
echo.

REM Install PyInstaller if not installed
pip install pyinstaller

REM Create executable file
pyinstaller --onefile --windowed --name="ScreenTranslator" ScreenTranslator.py

echo.
echo Build completed!
echo The executable file is located at: dist\ScreenTranslator.exe
echo.
echo You can copy the entire dist folder to test on other computers.
echo Make sure the target computer has:
echo - Tesseract OCR installed
echo - Ollama installed and running
echo.
pause
