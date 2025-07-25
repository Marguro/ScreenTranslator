# ScreenTranslator

A powerful desktop application for Windows that allows you to capture text from any area of your screen using OCR and get instant translations using local AI models via Ollama.

## Features

- **On-Demand Screen Capture**: Double-press the `Alt` key to instantly bring up a screen selection tool.
- **Accurate OCR**: Uses Tesseract to extract English text from any image, screenshot, or application on your screen.
- **Local AI Translation**: Leverages the power of local LLMs through Ollama for fast, private, and free translations to Thai.
- **Customizable Models**: Easily switch between different Ollama models (e.g., `gemma3n`, `deepseek-r1`) through the settings menu.
- **Convenient Overlay**: Displays the translation in a clean, scrollable, always-on-top window.
- **Clipboard Integration**: Automatically copies the translated text to your clipboard for easy pasting.
- **User-Friendly Controls**: A simple control panel to start selections, open settings, and exit the application.

## Requirements

- **Operating System**: Windows
- **Tesseract OCR**: Must be installed. You can download it from [here](https://github.com/UB-Mannheim/tesseract/wiki).
- **Ollama**: Must be installed and running. You can download it from [ollama.com](https://ollama.com/download).
- **Ollama Model**: At least one translation-capable model must be pulled. We recommend `gemma3n`.

## Installation and Setup

1.  **Install Tesseract OCR**:
    -   Download and run the installer from the [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page.
    -   **Important**: During installation, ensure the installation path is `C:\Program Files\Tesseract-OCR`. If you choose a different path, you must update the `tesseract_path` variable at the top of the `ScreenTranslator.py` script.

2.  **Install Ollama**:
    -   Download and install Ollama for Windows from the [official Ollama website](https://ollama.com/download).
    -   After installation, Ollama will run in the background.

3.  **Download an AI Model**:
    -   Open a Command Prompt or PowerShell terminal.
    -   Pull the recommended model by running the following command:
        ```sh
        ollama pull gemma3n
        ```
    -   You can also pull other models like `deepseek-r1`.

4.  **Run the Application**:
    -   Execute the `ScreenTranslator.py` script or the provided `.exe` file.

## How to Use

1.  **Launch**: Start the application. A "Screen Translator Controls" window will appear.
2.  **Select Area**: Press the `Alt` key twice quickly. The screen will dim, and your cursor will become a crosshair.
3.  **Capture**: Click and drag to draw a box around the English text you want to translate. Release the mouse button to confirm.
4.  **Get Translation**: A notification window will appear in the top-right corner of your screen, first showing "Extracting text..." then "Translating...", and finally displaying the Thai translation.
5.  **Paste**: The translated text is automatically copied to your clipboard. You can paste it anywhere you need.

## Controls

-   **Double `Alt` Key**: Activate the screen selection tool.
-   **`Esc` Key**: Cancel an active screen selection.
-   **Control Window Buttons**:
    -   `Select Screen Area`: Manually trigger the screen selection tool.
    -   `Settings`: Open the settings window to change the Ollama model.
-   **Close Button (X)** on the control window will exit the application.

## Troubleshooting

-   **"Tesseract OCR Missing" error**: This means the script cannot find `tesseract.exe`. Make sure you have installed it to `C:\Program Files\Tesseract-OCR` or have updated the `tesseract_path` variable in the script to point to the correct location.
-   **"Ollama Connection Issue" error**: This means the application cannot communicate with Ollama. Ensure the Ollama application is running on your computer. You can check for its icon in the system tray.
-   **Translation Error**: If you get a translation error, it might be because the selected Ollama model is not available or not running correctly. Use the `Settings` window to check the connection status and try a different model.
-   **Poor OCR Quality**: If the captured text is incorrect, try selecting a clearer, larger font. The application works best with standard digital text.
