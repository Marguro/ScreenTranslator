# Screen Translator

A modern, feature-rich desktop application for Windows that captures text from any area of your screen using OCR (Optical Character Recognition) and provides instant AI-powered translations using local language models via Ollama.

## ✨ Features

### 🖱️ **Intuitive Screen Capture**
- **Double Alt Hotkey**: Press Alt twice quickly to instantly activate screen selection
- **Visual Selection Tool**: Click and drag to select any area of your screen with real-time preview
- **Full-Screen Overlay**: Transparent overlay with visual feedback during selection
- **Escape to Cancel**: Press ESC to cancel selection at any time

### 🔍 **Advanced OCR Processing**
- **Tesseract Integration**: Uses industry-standard Tesseract OCR engine for accurate text extraction
- **Multi-PSM Support**: Automatically tries different page segmentation modes for optimal results
- **Grayscale Optimization**: Converts images to grayscale for improved OCR accuracy
- **Error Handling**: Comprehensive error reporting for OCR failures

### 🤖 **AI-Powered Translation**
- **Local AI Models**: Uses Ollama for private, offline translations
- **Multiple Model Support**: 
  - Gemma 3n (Standard)
  - Gemma 3n Unsloth (Optimized)
  - Phi3 Mini (Lightweight)
- **Optimized Parameters**: Model-specific temperature and token settings for best results
- **Background Processing**: Non-blocking translation using threaded workers

### 🎨 **Modern User Interface**
- **Dark Theme**: Beautiful Catppuccin-inspired color scheme
- **Floating Translation Window**: 
  - Draggable and resizable overlay
  - Smooth entrance animations
  - Always-on-top positioning
- **Control Panel**: Clean, minimalist main window
- **Settings Dialog**: Easy model switching and configuration
- **Status Indicators**: Real-time feedback on processing status

### 📋 **Productivity Features**
- **Auto-Clipboard**: Translated text automatically copied to clipboard
- **Copy Indicator**: Visual confirmation when text is copied
- **Scrollable Results**: Handle long translations with elegant scrolling
- **Persistent Overlay**: Translation window stays visible until closed

## 🛠️ Requirements

### System Requirements
- **Operating System**: Windows 10 or later
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for larger models)

### Required Software

#### Tesseract OCR
- **Download**: [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- **Installation Path**: Must be installed at `C:\Program Files\Tesseract-OCR\`
- **Note**: If installed elsewhere, update `TESSERACT_PATH` in the configuration

#### Ollama
- **Download**: [ollama.com](https://ollama.com/download)
- **Requirements**: Must be running in the background
- **Models**: At least one translation-capable model must be installed

### Python Dependencies
```
PyQt6
pytesseract
Pillow
mss
keyboard
pyperclip
ollama
```

## 📦 Installation

### 1. Install System Dependencies

**Install Tesseract OCR:**
```bash
# Download and run the installer from UB-Mannheim
# Ensure installation path is: C:\Program Files\Tesseract-OCR\
```

**Install Ollama:**
```bash
# Download from ollama.com and install
# Ollama will run automatically in the background
```

### 2. Install Ollama Models

Pull at least one translation model:
```bash
ollama pull gemma3n
# or
ollama pull phi3:mini
```

### 3. Install Python Dependencies

```bash
pip install PyQt6 pytesseract Pillow mss keyboard pyperclip ollama
```

### 4. Run the Application

```bash
python ScreenTranslator.py
```

## 🚀 Usage

### Quick Start
1. **Launch**: Run `python ScreenTranslator.py`
2. **Activate**: Press Alt twice quickly or click "📱 Capture Screen Area"
3. **Select**: Click and drag to select text area on screen
4. **Translate**: Wait for OCR extraction and AI translation
5. **Copy**: Translation is automatically copied to clipboard

### Interface Overview

#### Main Control Window
- **Capture Button**: Manually start screen selection
- **Settings Button**: Access model configuration and status
- **Hotkey Info**: Shows the Alt+Alt shortcut reminder

#### Translation Overlay
- **Draggable Header**: Click and drag the top area to move window
- **Resizable Borders**: Drag edges or corners to resize
- **Settings Access**: Click ⚙️ for quick model switching
- **Close Button**: ✕ to close the overlay

#### Screen Selector
- **Visual Feedback**: Transparent overlay with selection rectangle
- **Instructions**: On-screen guidance for selection
- **Real-time Preview**: See selected area as you drag

### Keyboard Shortcuts
- **Alt + Alt**: Activate screen selection (double-press within 0.5 seconds)
- **ESC**: Cancel screen selection
- **Mouse Drag**: Select area for translation

### Settings Configuration
- **Model Selection**: Choose from available Ollama models
- **Connection Status**: Real-time Ollama connectivity check
- **Model Information**: View available models and configuration

## ⚙️ Configuration

### Model Configuration
The application supports multiple AI models with optimized settings:

```python
AVAILABLE_MODELS = {
    "Gemma 3n": "gemma3n",
    "Gemma 3n (Unsloth)": "hf.co/unsloth/gemma-3n-E4B-it-GGUF:Q4_K_XL",
    "phi3 (mini)": "phi3:mini"
}
```

### Customization Options
- **Tesseract Path**: Update `TESSERACT_PATH` if installed elsewhere
- **Window Dimensions**: Modify `OVERLAY_WIDTH` and `OVERLAY_HEIGHT`
- **Hotkey Timing**: Adjust `ALT_DOUBLE_PRESS_THRESHOLD`
- **Model Parameters**: Fine-tune temperature and token limits per model

### Theme Customization
The application uses a modern dark theme with customizable colors:
- Primary: `#89b4fa` (Blue)
- Secondary: `#f38ba8` (Pink)
- Success: `#a6e3a1` (Green)
- Warning: `#fab387` (Orange)
- Background: `#1e1e2e` (Dark)

## 🐛 Troubleshooting

### Common Issues

**"Tesseract OCR not installed or not in PATH"**
- Ensure Tesseract is installed at `C:\Program Files\Tesseract-OCR\`
- Verify the executable exists at the specified path
- Update `TESSERACT_PATH` in code if using custom installation

**"Could not connect to Ollama"**
- Verify Ollama is installed and running
- Check if any models are pulled: `ollama list`
- Restart Ollama service if needed

**"No text detected" or Poor OCR Results**
- Ensure selected area contains clear, readable text
- Try selecting larger text or higher contrast areas
- Text should be primarily in English for best results

**Translation Errors**
- Verify the selected Ollama model supports translation
- Check if model is properly loaded: `ollama list`
- Try switching to a different model in settings

### Performance Tips
- **Larger Models**: Better translation quality but slower processing
- **Smaller Models**: Faster processing but potentially lower quality
- **Screen Resolution**: Higher DPI screens may need larger selection areas
- **Text Clarity**: Sharp, high-contrast text produces better OCR results

## 🏗️ Architecture

### Core Components
- **ScreenSelector**: Full-screen overlay for area selection
- **TranslationOverlay**: Floating window for displaying results
- **ControlWindow**: Main application control panel
- **OCRProcessor**: Handles Tesseract OCR operations
- **TranslationWorker**: Background thread for AI translation
- **KeyboardManager**: Global hotkey detection and handling

### Design Patterns
- **Threading**: Non-blocking UI with background processing
- **Signals/Slots**: Qt-based event handling
- **Modular Design**: Separate classes for distinct functionality
- **Configuration Management**: Centralized settings and styling

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional language support
- More AI model integrations
- Enhanced OCR preprocessing
- Cross-platform compatibility
- UI/UX improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## 🔗 Links

- **Tesseract OCR**: [GitHub Repository](https://github.com/tesseract-ocr/tesseract)
- **Ollama**: [Official Website](https://ollama.com/)
- **PyQt6**: [Documentation](https://doc.qt.io/qtforpython/)

## 🙏 Acknowledgments

- Tesseract OCR team for the excellent OCR engine
- Ollama team for making local AI accessible
- PyQt team for the robust GUI framework
- Contributors to all the open-source libraries used

---

**Made with ❤️ for seamless screen translation**
