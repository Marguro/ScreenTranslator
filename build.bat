@echo off
echo Building ScreenTranslator...

REM Clean previous build if exists
if exist "dist\ScreenTranslator" rmdir /s /q "dist\ScreenTranslator"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
pyinstaller --noconfirm --clean --optimize=1 ^
    --name="ScreenTranslator" ^
    --windowed ^
    --onedir ^
    --hidden-import=PyQt6 ^
    --hidden-import=pytesseract ^
    --hidden-import=mss ^
    --hidden-import=pyperclip ^
    --hidden-import=keyboard ^
    --hidden-import=ollama ^
    main.py

REM Copy manual files to the root of the build directory
copy "Manual\*" "dist\ScreenTranslator\"

echo Build completed successfully!
echo The executable is located in dist\ScreenTranslator\ScreenTranslator.exe