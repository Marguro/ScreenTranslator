@echo off
echo Building Screen Translator Executable...
echo.

REM Install PyInstaller if not installed
pip install pyinstaller

REM Create executable file in directory format (not single file)
pyinstaller --onedir --windowed --name="ScreenTranslator" ScreenTranslator.py

REM Copy Manual files to the build directory
echo.
echo Copying Manual files...
copy "Manual\*.html" "dist\ScreenTranslator\"


echo.
echo Build completed!
echo The executable file is located at: dist\ScreenTranslator\ScreenTranslator.exe
echo The _internal folder contains all dependencies: dist\ScreenTranslator\_internal\
echo Manual files copied: All HTML files from Manual folder
echo.
echo You can copy the entire dist\ScreenTranslator folder to test on other computers.
echo Make sure the target computer has:
echo - Tesseract OCR installed
echo - Ollama installed and running
echo.
pause
