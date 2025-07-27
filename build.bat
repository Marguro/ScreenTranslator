@echo off
echo Building ScreenTranslator...

REM Clean previous build if exists
if exist "dist\ScreenTranslator" rmdir /s /q "dist\ScreenTranslator"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
pyinstaller --noconfirm --clean ^
    --name="ScreenTranslator" ^
    --windowed ^
    --hidden-import=PyQt6 ^
    --hidden-import=pytesseract ^
    --hidden-import=mss ^
    --hidden-import=pyperclip ^
    --hidden-import=keyboard ^
    --hidden-import=ollama ^
    main.py

REM Create _internal folder
mkdir "dist\ScreenTranslator\_internal"

REM Copy manual files to the root of the build directory
copy "Manual\Manual.html" "dist\ScreenTranslator\"
copy "Manual\คู่มือ.html" "dist\ScreenTranslator\"

echo Build completed successfully!
echo The executable is located in dist\ScreenTranslator\ScreenTranslator.exe