# 🌍 Screen Translator

A real-time screen text translation application for Windows that uses OCR and AI technology to translate text accurately and quickly.

## 📋 Table of Contents

- [✨ Key Features](#-key-features)
  - [🖱️ Intuitive Screen Capture](#️-intuitive-screen-capture)
  - [🔍 Advanced OCR Processing](#-advanced-ocr-processing)
  - [🤖 AI-Powered Translation](#-ai-powered-translation)
  - [🎨 Modern User Interface](#-modern-user-interface)
  - [📋 Productivity Features](#-productivity-features)
- [🛠️ System Requirements](#️-system-requirements)
- [📦 Installation](#-installation)
- [🚀 Usage](#-usage)
- [⚙️ Configuration](#️-configuration)
- [🗂️ Project Structure](#️-project-structure)

## ✨ Key Features

### 🖱️ **Intuitive Screen Capture**
- **Double Alt Hotkey**: Press Alt twice quickly to activate screen area selection
- **Area Selection Tool**: Click and drag to select any area on screen with real-time preview
- **Transparent Overlay**: Clear visual feedback during area selection
- **Cancel with ESC**: Press ESC to cancel selection at any time

### 🔍 **Advanced OCR Processing**
- **Tesseract OCR Integration**: Uses industry-standard Tesseract OCR engine for accurate text extraction
- **Multi-PSM Support**: Tries different page segmentation modes for optimal results
- **Grayscale Optimization**: Converts images to grayscale to improve OCR accuracy
- **Error Handling**: Comprehensive error reporting system for OCR failures

### 🤖 **AI-Powered Translation**
- **Local AI Models**: Uses Ollama for offline and secure translation
- **Multiple Model Support**:
  - Gemma 3n (Standard)
  - Gemma 3n Unsloth (Optimized)
  - And other supported models
- **Optimized Parameters**: Model-specific temperature and token settings for best results
- **Background Processing**: Non-blocking translation using threaded workers

### 🎨 **Modern User Interface**
- **Dark Theme**: Beautiful Catppuccin-style dark theme
- **Floating Translation Window**:
  - Draggable and resizable
  - Smooth entrance animations
  - Always on top
- **Control Panel**: Clean and minimalist main window
- **Settings Dialog**: Easy model switching and configuration
- **Status Indicators**: Real-time processing feedback

### 📋 **Productivity Features**
- **Auto-Clipboard**: Translated text automatically copied to clipboard
- **Copy Indicator**: Visual confirmation when text is copied
- **Scrollable Results**: Handle long translations with elegant scrolling
- **Persistent Overlay**: Translation window stays visible until closed

## 🛠️ System Requirements

### System Specifications
- **Operating System**: Windows 10 or later
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for larger models)

### Required Software

#### 1. Tesseract OCR
- **Download**: [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- **Installation**: The program will automatically search for Tesseract in these locations:
  - `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
  - Or in system PATH
- **Note**: If installed in a different location, the program will show a warning on startup

#### 2. Ollama
- **Download**: [ollama.com](https://ollama.com/download)
- **Requirement**: Must be running in the background
- **Models**: At least one translation-capable model must be installed

### Python Dependencies
```
PyQt6>=6.4.0
Pillow>=9.0.0
pytesseract>=0.3.10
mss>=6.1.0
pyperclip>=1.8.2
keyboard>=0.13.5
ollama>=0.1.0
```

## 📦 Installation

### Method 1: Use Pre-built Executable (Recommended)

1. **Download build files**:
   - Go to `build/ScreenTranslator/` folder
   - Run `ScreenTranslator.exe`

### Method 2: Run from Source Code

#### 1. Install System Dependencies

**Install Tesseract OCR:**
1. Download from [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to default location (`C:\Program Files\Tesseract-OCR\`)

**Install Ollama:**
1. Download from [ollama.com](https://ollama.com/download)
2. Install and start the service
3. Install required models:
   ```bash
   ollama pull gemma3n
   # or
   ollama pull hf.co/unsloth/gemma-3n-E4B-it-GGUF:Q4_K_XL
   ```

#### 2. Install Python Dependencies

```bash
# Clone repository
git clone [repository-url]
cd ScreenTranslator

# Install dependencies
pip install -r requirements.txt
```

#### 3. Run the Program

```bash
python main.py
```

### Method 3: Build Executable

```bash
# Run build script
build.bat
```

The executable will be created in `build/ScreenTranslator/` folder

## 🚀 Usage

### Getting Started

1. **Launch the Program**:
   - Run `ScreenTranslator.exe` or `python main.py`
   - The control window will appear

2. **Check Settings**:
   - Click "Settings" to select desired AI model
   - Adjust font size as needed

### Translating Text

1. **Select Screen Area**:
   - Press **Alt twice quickly** (within 0.5 seconds)
   - Screen will switch to area selection mode

2. **Select Text**:
   - **Click and drag** to select area containing text
   - Real-time preview of selected area is shown

3. **Get Translation**:
   - Program will automatically process OCR and translate
   - Translation window will appear with results
   - Translated text is automatically copied to clipboard

### Managing Translation Window

- **Move**: Click and drag to move window
- **Resize**: Drag window corners to resize
- **Close**: Click X button or press ESC

### Hotkeys

| Key | Function |
|-----|----------|
| **Alt + Alt** | Activate screen area selection |
| **ESC** | Cancel area selection / Close translation window |
| **Ctrl+C** | Copy translated text (done automatically) |

## ⚙️ Configuration

### AI Model Selection

1. Open **Settings** from control window
2. Select model from list:
   - **Gemma 3n**: Standard model, suitable for general use
   - **Gemma 3n (Unsloth)**: Optimized model with better performance
3. Click **Save Settings**

### Font Customization

- Use slider in Settings window to adjust font size
- Font size range: 8-48 px (default: 16px)

### Settings File

Settings are saved in:
```
%USERPROFILE%\.screen_translator_settings.json
```

## 🗂️ Project Structure

```
ScreenTranslator/
├── main.py                 # Program entry point
├── requirements.txt        # Python dependencies
├── build.bat              # Script to build executable
├── ScreenTranslator.spec   # PyInstaller configuration
├── src/
│   ├── config/
│   │   └── config.py      # Configuration and settings
│   ├── core/
│   │   └── app.py         # Main application class
│   ├── ui/
│   │   ├── control_window.py     # Main control window
│   │   ├── screen_selector.py    # Screen area selection tool
│   │   ├── settings_dialog.py    # Settings window
│   │   ├── translation_overlay.py # Translation display window
│   │   └── ui_components.py      # General UI components
│   └── utils/
│       ├── keyboard_manager.py   # Keyboard shortcuts management
│       ├── ocr.py               # OCR processing
│       ├── style_manager.py     # Theme and style management
│       └── workers.py           # Background workers
├── build/
│   └── ScreenTranslator/    # Built executable files
└── Manual/                 # User manuals
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Tesseract OCR Not Found
**Symptom**: "Tesseract OCR Missing" warning message
**Solution**:
- Verify Tesseract is installed
- Check if it's in the correct location or system PATH

#### 2. Cannot Connect to Ollama
**Symptom**: "Ollama Connection Issue" warning message
**Solution**:
- Check if Ollama is running: `ollama list`
- Restart Ollama: `ollama serve`
- Verify models are installed

#### 3. Inaccurate OCR
**Solutions**:
- Select areas with clear text
- Avoid complex backgrounds
- Ensure text is appropriately sized

#### 4. Slow Translation
**Solutions**:
- Switch to a smaller model
- Check RAM and CPU usage
- Close unnecessary programs

### Debugging

To view debug information:
1. Open Command Prompt
2. Run program via: `python main.py`
3. View debug messages in console

## 🆕 Updates and Development

### Updates
- Check for new versions through repository
- Download new executable files or update source code

### Development
This project is open source and welcomes contributions:
- Bug reports
- Feature suggestions
- Code improvements

## 📄 License

See details in `LICENSE.txt`

## 🤝 Support

If you encounter issues or need help:
- Create an Issue in the repository
- Check Manual in `Manual/` folder
- Read the troubleshooting section in this document

---

**Note**: This program uses local AI models. Your data will not be sent to external servers.
