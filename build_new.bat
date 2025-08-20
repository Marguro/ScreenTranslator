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
    --icon="assest\icon.ico" ^
    --hidden-import=PyQt6 ^
    --hidden-import=pytesseract ^
    --hidden-import=mss ^
    --hidden-import=pyperclip ^
    --hidden-import=keyboard ^
    --hidden-import=ollama ^
    main.py

REM Copy manual files to the root of the build directory
copy "Manual\*" "dist\ScreenTranslator\"

REM Ensure assest folder exists in build and copy icon
if not exist "dist\ScreenTranslator\_internal\assest" mkdir "dist\ScreenTranslator\_internal\assest"
copy "assest\icon.ico" "dist\ScreenTranslator\_internal\assest\"

REM Create Desktop Shortcut using VBScript (more reliable)
echo Creating Desktop Shortcut...

REM Create temporary VBScript file
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sDesktop = oWS.SpecialFolders^("Desktop"^)
echo sLinkFile = sDesktop ^& "\Screen Translator.lnk"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%~dp0dist\ScreenTranslator\ScreenTranslator.exe"
echo oLink.WorkingDirectory = "%~dp0dist\ScreenTranslator"
echo oLink.IconLocation = "%~dp0dist\ScreenTranslator\_internal\assest\icon.ico"
echo oLink.Description = "AI-Powered Screen Translation Tool"
echo oLink.Save
) > CreateShortcut.vbs

REM Run VBScript to create shortcut
cscript //NoLogo CreateShortcut.vbs

REM Clean up temporary file
if exist CreateShortcut.vbs del CreateShortcut.vbs

echo.
echo ================================
echo Build completed successfully!
echo ================================
echo The executable is located in: dist\ScreenTranslator\ScreenTranslator.exe
echo Desktop shortcut created: Screen Translator.lnk
echo Manual files copied to build directory
echo.
echo You can now run the program from:
echo - Desktop shortcut: "Screen Translator"
echo - Direct execution: dist\ScreenTranslator\ScreenTranslator.exe
echo ================================
pause
