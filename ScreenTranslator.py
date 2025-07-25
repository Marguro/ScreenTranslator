import keyboard
import mss
from PIL import Image
import pytesseract
import ollama
import tkinter as tk
from tkinter import font, messagebox, StringVar, OptionMenu, scrolledtext
import pyperclip
import os
import sys
import threading
import time

# --- Constants and Configuration ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
AVAILABLE_MODELS = ["gemma3n", "deepseek-r1"]
ALT_DOUBLE_PRESS_THRESHOLD = 0.5  # seconds

class ScreenTranslatorApp:
    """
    An application for capturing a screen area, extracting text via OCR,
    and translating it using an Ollama-based LLM.
    """
    def __init__(self):
        # Core application state
        self.current_model = AVAILABLE_MODELS[0]
        self.last_alt_press_time = 0
        self.is_exiting = False

        # Tkinter UI elements
        self.root = None
        self.control_window = None
        self.translation_window = None
        self.translation_label = None
        self.settings_window = None
        self.model_var = None

        # Screen selection elements
        self.selection_window = None
        self.canvas = None
        self.selection_rect = None
        self.selection_start_x = 0
        self.selection_start_y = 0

        # Additional instance variables for overlay dragging
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.overlay_width = 500
        self.overlay_height = 200
        self.overlay_x = 0
        self.overlay_y = 0

        self._initialize_tesseract()

    def _initialize_tesseract(self):
        """Checks for Tesseract installation and sets the command path."""
        if os.path.exists(TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        else:
            print("WARNING: Tesseract OCR not found at the specified path.")
            print(f"Expected path: {TESSERACT_PATH}")

    # --- Service-like Methods ---

    def _translate_text(self, text_to_translate: str) -> str:
        """Translates text using the selected Ollama model."""
        if not text_to_translate:
            return "ไม่มีข้อความที่จะแปล"

        prompt = f'แปลข้อความต่อไปนี้เป็นภาษาไทย โดยไม่ต้องอธิบายหรือแปลความหมายเพิ่มเติม):\n"{text_to_translate}"\n\nThai Translation:'
        try:
            print(f"[INFO] Attempting translation with model: {self.current_model}")
            response = ollama.generate(
                model=self.current_model,
                prompt=prompt,
                options={'temperature': 0.1, 'num_predict': 200}
            )
            translated_text = response['response'].strip()
            if not any('\u0e00' <= char <= '\u0e7f' for char in translated_text):
                return f"Translation Error: ตัวอักษรไม่ถูกต้อง\n\nOriginal response: {translated_text}"
            return translated_text
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return f"Translation Error: {e}"

    def _get_text_from_screen_area(self, x, y, width, height):
        """Captures a screen area and extracts text using Tesseract OCR."""
        try:
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb).convert('L')
                text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
                return text.strip()
        except pytesseract.pytesseract.TesseractNotFoundError:
            return "ERROR: Tesseract OCR not installed or not in PATH"
        except Exception as e:
            return f"Error capturing text: {str(e)}"

    # --- Core Application Logic ---

    def _process_selected_area(self, x, y, width, height):
        """Orchestrates the OCR and translation process for a selected area."""
        self._update_translation_display("กำลังสกัดข้อความจากภาพ...")
        captured_text = self._get_text_from_screen_area(x, y, width, height)
        print(f"[INFO] Captured Text: '{captured_text}'")

        if captured_text and not captured_text.startswith("ERROR:"):
            self._update_translation_display("กำลังแปล...")
            translated_text = self._translate_text(captured_text)
            print(f"[INFO] Translated Text: '{translated_text}'")
            self._update_translation_display(translated_text)
        else:
            error_msg = captured_text if captured_text.startswith("ERROR:") else "ไม่พบข้อความที่จะแปล หรือการดึงข้อความล้มเหลว"
            print(f"[INFO] {error_msg}")
            self._update_translation_display(error_msg)

    # --- UI Creation and Management ---

    def _create_control_window(self):
        """Creates the main control panel for the application."""
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Screen Translator")
        self.control_window.geometry(f"300x160+{self.root.winfo_screenwidth() // 2 - 150}+{self.root.winfo_screenheight() // 2 - 80}")
        self.control_window.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)

        tk.Label(self.control_window, text="Screen Translator", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Button(self.control_window, text="Select Screen Area (Double Alt)", command=self._start_screen_selection).pack(fill="x", padx=20, pady=5)
        tk.Button(self.control_window, text="Settings", command=self._show_settings).pack(fill="x", padx=20, pady=5)

    def _create_translation_overlay(self):
        """Creates or recreates the floating window to display translations."""
        if self.translation_window and self.translation_window.winfo_exists():
            self.translation_window.destroy()

        self.translation_window = tk.Toplevel(self.root)
        self.translation_window.overrideredirect(True)
        self.translation_window.attributes('-alpha', 0.9, '-topmost', True)

        # Default position on first creation
        if self.overlay_x == 0 and self.overlay_y == 0:
            screen_width = self.translation_window.winfo_screenwidth()
            self.overlay_x = screen_width - self.overlay_width - 20
            self.overlay_y = 20

        self.translation_window.geometry(f"{self.overlay_width}x{self.overlay_height}+{self.overlay_x}+{self.overlay_y}")

        # Main frame for content that can be dragged
        main_frame = tk.Frame(self.translation_window, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add resize grip at bottom-right corner
        sizegrip = tk.Label(main_frame, text="◢", bg="black", fg="white", cursor="sizing")
        sizegrip.pack(side=tk.BOTTOM, anchor=tk.SE, padx=5, pady=5)

        # Make window draggable from the header
        button_frame = tk.Frame(main_frame, bg="black")
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add a drag handle
        drag_label = tk.Label(button_frame, text="≡", bg="black", fg="white", cursor="fleur")
        drag_label.pack(side=tk.LEFT, padx=5)

        # Buttons
        tk.Button(button_frame, text="✖", command=lambda: self.translation_window.destroy(),
                  font=("Arial", 10), bg="black", fg="white").pack(side=tk.RIGHT)
        tk.Button(button_frame, text="⚙️", command=self._show_settings,
                  font=("Arial", 10), bg="black", fg="white").pack(side=tk.RIGHT, padx=5)

        # Content area
        self.translation_label = scrolledtext.ScrolledText(
            main_frame, bg="black", fg="white", font=("Arial", 14, "bold"),
            wrap=tk.WORD, padx=10, pady=10
        )
        self.translation_label.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        self.translation_label.config(state=tk.DISABLED)

        # Bind events for dragging
        drag_label.bind("<ButtonPress-1>", self._start_drag)
        drag_label.bind("<ButtonRelease-1>", self._stop_drag)
        drag_label.bind("<B1-Motion>", self._on_drag)

        # Bind events for resizing
        sizegrip.bind("<ButtonPress-1>", self._start_resize)
        sizegrip.bind("<ButtonRelease-1>", self._stop_resize)
        sizegrip.bind("<B1-Motion>", self._on_resize)

        self.translation_window.focus_set()

    def _start_drag(self, event):
        """Begins drag operation for overlay window"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_drag(self, event):
        """Handles dragging of the overlay window"""
        x = self.translation_window.winfo_x() + (event.x - self.drag_data["x"])
        y = self.translation_window.winfo_y() + (event.y - self.drag_data["y"])
        self.translation_window.geometry(f"+{x}+{y}")
        # Store position for future window creations
        self.overlay_x = x
        self.overlay_y = y

    def _stop_drag(self, event):
        """Ends drag operation"""
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

    def _start_resize(self, event):
        """Begins resize operation"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_resize(self, event):
        """Handles resizing of the overlay window"""
        width = max(300, self.overlay_width + (event.x - self.drag_data["x"]))
        height = max(150, self.overlay_height + (event.y - self.drag_data["y"]))
        self.translation_window.geometry(f"{width}x{height}")
        # Store size for future window creations
        self.overlay_width = width
        self.overlay_height = height
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _stop_resize(self, event):
        """Ends resize operation"""
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

    def _update_translation_display(self, text):
        """Updates the text in the translation overlay window."""
        if not self.translation_window or not self.translation_window.winfo_exists():
            self._create_translation_overlay()

        self.translation_label.config(state=tk.NORMAL)
        self.translation_label.delete(1.0, tk.END)
        self.translation_label.insert(tk.END, text)
        self.translation_label.config(state=tk.DISABLED)
        self.translation_window.update()
        pyperclip.copy(text)

    def _show_settings(self):
        """Displays the settings window for model selection."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x250")
        self.settings_window.attributes('-topmost', True)

        # Center the settings window on screen
        screen_width = self.settings_window.winfo_screenwidth()
        screen_height = self.settings_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.settings_window.geometry(f"+{x}+{y}")

        tk.Label(self.settings_window, text="Select Ollama Model:").pack(pady=(20, 5))
        self.model_var = StringVar(value=self.current_model)
        OptionMenu(self.settings_window, self.model_var, *AVAILABLE_MODELS).pack(pady=5)
        tk.Button(self.settings_window, text="Save Settings", command=self._save_settings).pack(pady=20)

        status_label = tk.Label(self.settings_window, text="Checking Ollama status...")
        status_label.pack(pady=10)
        try:
            models = ollama.list().get('models', [])
            status_text = f"Ollama is running with {len(models)} models."
        except Exception as e:
            status_text = f"Ollama error: {e}\nMake sure Ollama is installed and running."
        status_label.config(text=status_text)

    def _save_settings(self):
        """Saves the selected model from the settings window."""
        self.current_model = self.model_var.get()
        print(f"[INFO] Changed model to: {self.current_model}")
        if self.settings_window:
            self.settings_window.destroy()

    # --- Screen Selection Methods ---

    def _start_screen_selection(self):
        """Creates a transparent, fullscreen window for area selection."""
        if self.selection_window and self.selection_window.winfo_exists():
            return

        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True, '-alpha', 0.45, '-topmost', True) # Semi-transparent fullscreen
        self.selection_window.bind("<Escape>", lambda e: self.selection_window.destroy())

        self.canvas = tk.Canvas(self.selection_window, cursor="cross", bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_selection_start)
        self.canvas.bind("<B1-Motion>", self._on_selection_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_selection_complete)

        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2, 30,
            text="Click and drag to select area. Press ESC to cancel.",
            fill="white", font=("Arial", 16, "bold")
        )

    def _on_selection_start(self, event):
        """Records the starting coordinates of the selection."""
        self.selection_start_x, self.selection_start_y = event.x, event.y
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="white", fill="white", dash=(4, 2), width=3
        )

    def _on_selection_motion(self, event):
        """Updates the selection rectangle as the mouse moves."""
        if self.selection_rect:
            self.canvas.coords(self.selection_rect, self.selection_start_x, self.selection_start_y, event.x, event.y)

    def _on_selection_complete(self, event):
        """Finalizes selection, captures area, and triggers processing."""
        if self.selection_window:
            x1, y1 = min(self.selection_start_x, event.x), min(self.selection_start_y, event.y)
            x2, y2 = max(self.selection_start_x, event.x), max(self.selection_start_y, event.y)
            self.selection_window.destroy()

            if (x2 - x1) > 10 and (y2 - y1) > 10:
                self._process_selected_area(x1, y1, x2 - x1, y2 - y1)
            else:
                print("[INFO] Selection too small, ignored.")

    # --- Hotkey and Exit Handling ---

    def _on_alt_pressed(self, e):
        """Detects a double press of the Alt key."""
        if e.event_type == keyboard.KEY_DOWN and e.name == 'alt':
            current_time = time.time()
            if 0.1 < (current_time - self.last_alt_press_time) < ALT_DOUBLE_PRESS_THRESHOLD:
                print("\n[INFO] Double Alt detected! Starting screen selection...")
                self.root.after(0, self._start_screen_selection)
            self.last_alt_press_time = current_time

    def _cleanup_and_exit(self):
        """Safely closes all resources and exits the application."""
        if self.is_exiting:
            return
        self.is_exiting = True
        print("Exiting program...")
        try:
            keyboard.unhook_all()
        except Exception as e:
            print(f"Could not unhook keyboard: {e}")

        if self.root:
            self.root.quit()
        os._exit(0)

    # --- Main Execution ---

    def run(self):
        """Initializes and runs the application."""
        print("Screen Translator Program Started.")
        print("Press Alt twice quickly to select screen area.")

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Screen Translator")
        self.root.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)

        self._create_control_window()

        # Initial checks
        if not os.path.exists(TESSERACT_PATH):
            messagebox.showwarning("Tesseract OCR Missing", "Tesseract OCR not found. Please install it and configure the TESSERACT_PATH.")
        try:
            ollama.list()
        except Exception as e:
            messagebox.showwarning("Ollama Connection Issue", f"Could not connect to Ollama: {e}\nPlease ensure it is installed and running.")

        keyboard.on_press(self._on_alt_pressed)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nProgram interrupted.")
        finally:
            self._cleanup_and_exit()

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    app.run()
