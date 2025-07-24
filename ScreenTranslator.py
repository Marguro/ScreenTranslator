import keyboard
import mss
from PIL import Image
import pytesseract
import ollama
import tkinter as tk
from tkinter import font, messagebox, StringVar, OptionMenu, scrolledtext
import pyperclip # For fallback / convenience
import os
import sys
import threading
import time  # Import time module for tracking double-press

# --- Ollama / LLM Integration ---
# List of available models to try (in order of preference)
AVAILABLE_MODELS = [
    "gemma3n",
    "deepseek-r1"
]

# Current model selection
current_model = AVAILABLE_MODELS[0]  # Default to first model

def translate_text(text_to_translate: str) -> str:
    global current_model

    if not text_to_translate:
        return "ไม่มีข้อความที่จะแปล"

    # Use a clearer prompt specifically asking for Thai translation
    prompt = f"""แปลข้อความต่อไปนี้เป็นภาษาไทย โดยไม่ต้องอธิบายหรือแปลความหมายเพิ่มเติม):
"{text_to_translate}"

Thai Translation:"""

    try:
        print(f"[INFO] Attempting translation with model: {current_model}")
        response = ollama.generate(
            model=current_model,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 200
            }
        )

        translated_text = response['response'].strip()

        # If no Thai characters in response, it might have failed
        if not any('\u0e00' <= char <= '\u0e7f' for char in translated_text):
            return f"Translation Error: ไม่พบตัวอักษรภาษาไทย\n\nOriginal response: {translated_text}"

        return translated_text

    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return f"Translation Error: {e}"

# --- Screen Capture & OCR ---
# Configure Tesseract path - update this to your actual Tesseract installation path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("WARNING: Tesseract OCR not found at expected location.")
    print("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("Then update the tesseract_path in this script.")

def get_text_from_screen_area(x, y, width, height):
    try:
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            # Apply some image preprocessing to improve OCR accuracy
            # Convert to grayscale
            img = img.convert('L')

            # Use multiple language models for better accuracy
            text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
            return text.strip()
    except pytesseract.pytesseract.TesseractNotFoundError:
        return "ERROR: Tesseract OCR not installed or not in PATH"
    except Exception as e:
        return f"Error capturing text: {str(e)}"

# Variables for screen selection
selection_start_x = 0
selection_start_y = 0
selection_rect = None
selection_window = None
canvas = None

# Add screen selection functionality
def start_screen_selection():
    global selection_window, canvas, selection_rect, root

    if selection_window and selection_window.winfo_exists():
        selection_window.destroy()

    # Create a fullscreen transparent window for selection
    selection_window = tk.Toplevel(root)
    selection_window.attributes('-fullscreen', True)
    selection_window.attributes('-alpha', 0.3)
    selection_window.attributes('-topmost', True)

    # Create canvas for drawing selection rectangle with black background
    canvas = tk.Canvas(selection_window, cursor="cross", bg="black")
    canvas.pack(fill=tk.BOTH, expand=True)

    # Bind mouse events
    canvas.bind("<ButtonPress-1>", on_selection_start)
    canvas.bind("<B1-Motion>", on_selection_motion)
    canvas.bind("<ButtonRelease-1>", on_selection_complete)

    # Bind escape key to cancel
    selection_window.bind("<Escape>", lambda e: selection_window.destroy())

    # Instructions (kept white text for visibility on black background)
    canvas.create_text(
        selection_window.winfo_screenwidth() // 2,
        30,
        text="Click and drag to select the area to capture. Press ESC to cancel.",
        fill="white",
        font=("Arial", 16, "bold")
    )

def on_selection_start(event):
    global selection_start_x, selection_start_y, selection_rect
    selection_start_x, selection_start_y = event.x, event.y

    # Create initial rectangle
    if selection_rect:
        canvas.delete(selection_rect)
    selection_rect = canvas.create_rectangle(
        selection_start_x, selection_start_y,
        selection_start_x, selection_start_y,
        fill="white",
        dash = (4,2),
        width=3  # Slightly thicker line for better visibility
    )

def on_selection_motion(event):
    global selection_rect
    if selection_rect:
        canvas.coords(selection_rect, selection_start_x, selection_start_y, event.x, event.y)

def on_selection_complete(event):
    global selection_window

    if selection_window:
        # Get coordinates, ensuring positive width and height
        x1, y1 = selection_start_x, selection_start_y
        x2, y2 = event.x, event.y

        # Adjust coordinates if dragged in reverse direction
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        # Calculate width and height
        width = x2 - x1
        height = y2 - y1

        # Close selection window
        selection_window.destroy()

        # Only process if selection has reasonable size
        if width > 10 and height > 10:
            process_selected_area(x1, y1, width, height)
        else:
            print("[INFO] Selection too small, ignored")

def process_selected_area(x, y, width, height):
    # Show translation is in progress
    update_translation_display("กำลังสกัดข้อความจากภาพ...")

    # Get text from selected area
    captured_text = get_text_from_screen_area(x, y, width, height)
    print(f"[INFO] Captured Text: '{captured_text}'")

    if captured_text and not captured_text.startswith("ERROR:"):
        # Show working status
        update_translation_display("กำลังแปล...")

        # Perform translation
        translated_text = translate_text(captured_text)
        print(f"[INFO] Translated Text: '{translated_text}'")
        update_translation_display(translated_text)
    else:
        print("[INFO] No text captured or OCR failed.")
        update_translation_display(captured_text if captured_text.startswith("ERROR:") else "ไม่พบข้อความที่จะแปล หรือการดึงข้อความล้มเหลว")

# --- Translation Overlay GUI (Tkinter) ---
root = None  # Main Tkinter root window
translation_window = None
translation_label = None
settings_window = None
model_var = None

# Add system tray icon and exit menu
def create_system_tray():
    global root

    # Create a small control window that will be shown in taskbar
    control_window = tk.Toplevel(root)
    control_window.title("Screen Translator")
    control_window.geometry("300x200")  # Reduced height since we removed a button
    control_window.protocol("WM_DELETE_WINDOW", exit_program)

    # Create buttons for main controls
    tk.Label(control_window, text="Screen Translator Controls", font=("Arial", 12, "bold")).pack(pady=10)

    # Update button text to show new hotkey (double Alt)
    tk.Button(control_window, text="Select Screen Area (Double Alt)",
              command=start_screen_selection).pack(fill="x", padx=20, pady=5)

    tk.Button(control_window, text="Settings",
              command=show_settings).pack(fill="x", padx=20, pady=5)


    return control_window

def exit_program():
    print("Exiting program via exit button...")
    cleanup_and_exit()

def cleanup_and_exit():
    global root, translation_window, settings_window

    # Unregister hotkeys if possible
    try:
        keyboard.unhook_all()
    except:
        pass

    # Set a flag to prevent recursive calls
    if hasattr(cleanup_and_exit, 'is_exiting'):
        return
    cleanup_and_exit.is_exiting = True

    # Close windows safely
    try:
        if translation_window:
            try:
                translation_window.destroy()
            except:
                pass

        if settings_window:
            try:
                settings_window.destroy()
            except:
                pass

        if root:
            try:
                root.quit()  # Use quit instead of destroy to properly end mainloop
            except:
                pass
    except:
        pass

    print("Program Exited.")

    # Use os._exit to force exit without raising SystemExit
    os._exit(0)

def create_translation_overlay():
    global translation_window, translation_label, root

    # Create root window if it doesn't exist
    if root is None or not root.winfo_exists():
        root = tk.Tk()
        root.withdraw()  # Hide the main window

    if translation_window and translation_window.winfo_exists():
        translation_window.destroy()

    translation_window = tk.Toplevel(root)
    translation_window.overrideredirect(True)
    translation_window.attributes('-alpha', 0.9)
    translation_window.attributes('-topmost', True)

    screen_width = translation_window.winfo_screenwidth()
    window_width = 500
    window_height = 200  # Increased height for scrollable area
    x_pos = screen_width - window_width - 20
    y_pos = 20
    translation_window.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

    # Force the window to update and appear
    translation_window.update()

    # Create a frame for the buttons
    button_frame = tk.Frame(translation_window, bg="black")
    button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Add a settings button to the frame
    settings_btn = tk.Button(button_frame, text="⚙️", command=show_settings,
                          font=("Arial", 10), bg="black", fg="white")
    settings_btn.pack(side=tk.RIGHT, padx=5)

    # Add a close button to the frame
    close_btn = tk.Button(button_frame, text="✖", command=lambda: translation_window.destroy(),
                        font=("Arial", 10), bg="black", fg="white")
    close_btn.pack(side=tk.RIGHT, padx=5)

    # Create custom font
    custom_font = font.Font(family="Arial", size=14, weight="bold")

    # Create a scrolled text widget instead of a label
    translation_label = scrolledtext.ScrolledText(
        translation_window,
        bg="black",
        fg="yellow",
        font=custom_font,
        wrap=tk.WORD,
        padx=10,
        pady=10
    )
    translation_label.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    # Make the text widget read-only but allow selection
    translation_label.config(state=tk.DISABLED)

    translation_window.bind("<FocusOut>", lambda e: None)  # Don't auto-close on focus out
    translation_window.bind("<Escape>", lambda e: translation_window.destroy())
    translation_window.focus_set()

def show_settings():
    global settings_window, model_var, current_model

    if settings_window and settings_window.winfo_exists():
        settings_window.destroy()

    settings_window = tk.Toplevel(root)
    settings_window.title("Screen Translator Settings")
    settings_window.geometry("400x300")
    settings_window.attributes('-topmost', True)

    # Model selection
    tk.Label(settings_window, text="Select Ollama Model:").pack(pady=(20, 5))

    model_var = StringVar(value=current_model)
    model_menu = OptionMenu(settings_window, model_var, *AVAILABLE_MODELS)
    model_menu.pack(pady=5)

    # Save button
    tk.Button(settings_window, text="Save Settings",
              command=lambda: save_settings(model_var.get())).pack(pady=20)

    # Status text
    status_label = tk.Label(settings_window, text="Current status: Checking Ollama...")
    status_label.pack(pady=10)

    # Check Ollama status
    try:
        models = ollama.list()
        available_models = [m['name'] for m in models.get('models', [])]
        status_text = f"Ollama is running with {len(available_models)} models."
        if available_models:
            status_text += f"\nAvailable models: {', '.join(available_models[:3])}"
            if len(available_models) > 3:
                status_text += f" and {len(available_models)-3} more."
    except Exception as e:
        status_text = f"Ollama error: {str(e)}\n\nMake sure Ollama is installed and running."

    status_label.config(text=status_text)

def save_settings(selected_model):
    global current_model, settings_window
    current_model = selected_model
    print(f"[INFO] Changed model to: {current_model}")
    if settings_window:
        settings_window.destroy()

def update_translation_display(text):
    global translation_window, translation_label
    if not translation_window or not translation_window.winfo_exists():
        create_translation_overlay()
    if translation_label:
        # Enable editing, clear content, insert new text, then disable again
        translation_label.config(state=tk.NORMAL)
        translation_label.delete(1.0, tk.END)
        translation_label.insert(tk.END, text)
        translation_label.config(state=tk.DISABLED)

        # Force update to make sure window is visible
        translation_window.update()
    pyperclip.copy(text) # Also copy to clipboard for convenience

# --- Main Hotkey Handler ---
# Variables to track double Alt press
last_alt_press_time = 0
ALT_DOUBLE_PRESS_THRESHOLD = 0.5  # seconds

def on_alt_pressed(e):
    global last_alt_press_time

    # Check if this is a press (not a release)
    if e.event_type == keyboard.KEY_DOWN and e.name == 'alt':
        current_time = time.time()
        time_diff = current_time - last_alt_press_time

        # If pressed within threshold, consider it a double press
        if 0.1 < time_diff < ALT_DOUBLE_PRESS_THRESHOLD:
            print("\n[INFO] Double Alt detected! Starting screen selection...")
            # Run in main thread for Tkinter
            if threading.current_thread() is not threading.main_thread():
                root.after(0, start_screen_selection)
            else:
                start_screen_selection()

        # Update last press time
        last_alt_press_time = current_time

def show_settings_hotkey():
    print("[INFO] Settings hotkey pressed")
    if threading.current_thread() is not threading.main_thread():
        root.after(0, show_settings)
    else:
        if not translation_window or not translation_window.winfo_exists():
            create_translation_overlay()
        show_settings()


# --- Program Start ---
if __name__ == "__main__":
    print("Screen Translator Program Started.")
    print("Press Alt twice quickly to select screen area.")
    print("Press Ctrl+Alt+S for settings.")
    print("Press Ctrl+Alt+Q to exit program.")
    print("Press Ctrl+C in terminal to exit.")

    # Initialize Tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Set window title so it appears in Alt+Tab
    root.title("Screen Translator")

    # Add app icon
    try:
        root.iconbitmap("icon.ico")  # You'll need to create/add an icon file
    except:
        pass  # Ignore if icon not found

    # Create visible control window
    control_window = create_system_tray()

    # Verify Tesseract installation first
    if not os.path.exists(tesseract_path):
        messagebox.showwarning(
            "Tesseract OCR Missing",
            "Tesseract OCR is not installed or not found at the expected location.\n\n"
            "Please install it from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Then update the tesseract_path in this script."
        )

    # Check if Ollama is running
    try:
        ollama.list()
    except Exception as e:
        messagebox.showwarning(
            "Ollama Connection Issue",
            f"Could not connect to Ollama: {str(e)}\n\n"
            "Please make sure Ollama is installed and running.\n"
            "Download from: https://ollama.com/download"
        )

    # Register hotkeys
    # Remove the old Ctrl+Alt+T hotkey
    # keyboard.add_hotkey('ctrl+alt+t', on_hotkey_pressed)

    # Add listener for Alt key to detect double-press
    keyboard.on_press(on_alt_pressed)

    # Handle Ctrl+C in terminal
    try:
        root.protocol("WM_DELETE_WINDOW", exit_program)  # Handle window close
        root.mainloop()  # Use Tkinter mainloop for proper GUI handling
    except KeyboardInterrupt:
        print("\nProgram interrupted and exiting.")
    except SystemExit:
        # Catch SystemExit to avoid the second exception
        print("Exiting gracefully...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cleanup_and_exit()