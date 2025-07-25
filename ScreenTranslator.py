import keyboard
import mss
from PIL import Image
import pytesseract
import ollama
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, scrolledtext
import pyperclip
import os
import time

# --- Constants and Configuration ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
AVAILABLE_MODELS = ["gemma3n"]
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
        self.overlay_width = 600  # Increased from 500
        self.overlay_height = 300  # Increased from 200
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

    @staticmethod
    def _get_text_from_screen_area(x, y, width, height):
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
        self.control_window.geometry("320x200")

        # Center the window on screen
        screen_width = self.control_window.winfo_screenwidth()
        screen_height = self.control_window.winfo_screenheight()
        x = (screen_width - 320) // 2
        y = (screen_height - 200) // 2
        self.control_window.geometry(f"320x200+{x}+{y}")

        self.control_window.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)
        self.control_window.resizable(False, False)

        # Modern color scheme
        bg_color = "#1e1e2e"  # Dark background
        accent_color = "#89b4fa"  # Blue accent
        text_color = "#cdd6f4"  # Light text
        button_bg = "#313244"  # Button background
        button_hover = "#45475a"  # Button hover

        self.control_window.configure(bg=bg_color)

        # Main container with padding
        main_frame = tk.Frame(self.control_window, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        header_frame = tk.Frame(main_frame, bg=bg_color)
        header_frame.pack(fill="x", pady=(0, 20))

        # App title with modern styling
        title_label = tk.Label(
            header_frame,
            text="Screen Translator",
            font=("Segoe UI", 16, "bold"),
            fg=accent_color,
            bg=bg_color
        )
        title_label.pack()

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="OCR • Translation • AI",
            font=("Segoe UI", 9),
            fg=text_color,
            bg=bg_color
        )
        subtitle_label.pack(pady=(2, 0))

        # Buttons section
        buttons_frame = tk.Frame(main_frame, bg=bg_color)
        buttons_frame.pack(fill="x")

        # Custom button style function
        def create_modern_button(parent, text, command, icon=""):
            btn_frame = tk.Frame(parent, bg=button_bg, relief="flat", bd=0)
            btn_frame.pack(fill="x", pady=3)

            # Add some padding inside the button frame
            inner_frame = tk.Frame(btn_frame, bg=button_bg)
            inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

            button = tk.Button(
                inner_frame,
                text=f"{icon} {text}",
                command=command,
                font=("Segoe UI", 10),
                fg=text_color,
                bg=button_bg,
                activebackground=button_hover,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=20,
                pady=12,
                cursor="hand2"
            )
            button.pack(fill="both", expand=True)

            # Hover effects
            def on_enter(e):
                button.configure(bg=button_hover, fg="#ffffff")

            def on_leave(e):
                button.configure(bg=button_bg, fg=text_color)

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)

            return btn_frame

        # Create modern buttons
        create_modern_button(
            buttons_frame,
            "Capture Screen Area",
            self._start_screen_selection,
            "📱"
        )

        create_modern_button(
            buttons_frame,
            "Settings",
            self._show_settings,
            "⚙️"
        )

        # Status/Info section
        status_frame = tk.Frame(main_frame, bg=bg_color)
        status_frame.pack(fill="x", pady=(15, 0))

        # Hotkey info
        hotkey_label = tk.Label(
            status_frame,
            text="💡 Press Alt twice quickly to capture",
            font=("Segoe UI", 8),
            fg="#6c7086",  # Muted text color
            bg=bg_color
        )
        hotkey_label.pack()

        # Add a subtle separator line
        separator = tk.Frame(main_frame, height=1, bg="#45475a")
        separator.pack(fill="x", pady=(10, 5))

        # Version/Credit
        credit_label = tk.Label(
            main_frame,
            text="v1.0 • AI-Powered Translation",
            font=("Segoe UI", 7),
            fg="#6c7086",
            bg=bg_color
        )
        credit_label.pack(pady=(5, 0))

    def _create_translation_overlay(self):
        """Creates or recreates the floating window to display translations."""
        if self.translation_window and self.translation_window.winfo_exists():
            self.translation_window.destroy()

        self.translation_window = tk.Toplevel(self.root)
        self.translation_window.overrideredirect(True)
        self.translation_window.attributes('-alpha', 0.95, '-topmost', True)

        # Default position on first creation - FIXED positioning
        if self.overlay_x == 0 and self.overlay_y == 0:
            screen_width = self.translation_window.winfo_screenwidth()
            screen_height = self.translation_window.winfo_screenheight()
            # Leave more space from edges to ensure resize grip is visible
            self.overlay_x = screen_width - self.overlay_width - 50  # More space from right edge
            self.overlay_y = 50  # More space from top

            # Make sure window doesn't go off screen
            if self.overlay_x < 0:
                self.overlay_x = 50
            if self.overlay_y + self.overlay_height > screen_height - 100: # Leave space for taskbar
                self.overlay_y = screen_height - self.overlay_height - 100

        self.translation_window.geometry(f"{self.overlay_width}x{self.overlay_height}+{self.overlay_x}+{self.overlay_y}")

        # Modern color scheme (matching the app theme)
        bg_color = "#1e1e2e"  # Dark background
        accent_color = "#89b4fa"  # Blue accent
        text_color = "#cdd6f4"  # Light text
        header_bg = "#313244"  # Header background
        button_hover = "#45475a"  # Button hover

        # Main frame with modern styling
        main_frame = tk.Frame(self.translation_window, bg=bg_color, relief="flat", bd=2)
        main_frame.pack(fill="both", expand=True)

        # Header section with drag handle and controls
        header_frame = tk.Frame(main_frame, bg=header_bg, height=35)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        # Left side - drag handle and title
        left_header = tk.Frame(header_frame, bg=header_bg)
        left_header.pack(side="left", fill="both", expand=True)

        # Drag handle with better styling
        drag_label = tk.Label(
            left_header,
            text="⋮⋮",
            bg=header_bg,
            fg=text_color,
            cursor="fleur",
            font=("Segoe UI", 12),
            padx=8
        )
        drag_label.pack(side="left", pady=8)

        # Window title
        title_label = tk.Label(
            left_header,
            text="🌐 Translation",
            bg=header_bg,
            fg=accent_color,
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        )
        title_label.pack(side="left", fill="both", expand=True, pady=8)

        # Right side - control buttons
        right_header = tk.Frame(header_frame, bg=header_bg)
        right_header.pack(side="right", fill="y")

        # Custom button style for header buttons
        def create_header_button(parent, text, command, color="#f38ba8"):
            btn = tk.Button(
                parent,
                text=text,
                command=command,
                font=("Segoe UI", 9, "bold"),
                fg=text_color,
                bg=header_bg,
                activebackground=button_hover,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=8,
                pady=0,
                cursor="hand2",
                width=3
            )
            btn.pack(side="right", padx=1, fill="y")

            def on_enter(e):
                btn.configure(bg=color, fg="#ffffff")

            def on_leave(e):
                btn.configure(bg=header_bg, fg=text_color)

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

            return btn

        # Control buttons with hover colors
        create_header_button(right_header, "✕", lambda: self.translation_window.destroy(), "#f38ba8")  # Red
        create_header_button(right_header, "⚙", self._show_settings, "#fab387")  # Orange

        # Content area with modern styling
        content_frame = tk.Frame(main_frame, bg=bg_color)
        content_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Text area with modern scrolled text
        self.translation_label = scrolledtext.ScrolledText(
            content_frame,
            bg="#313244",  # Slightly lighter than main bg
            fg=text_color,
            font=("Segoe UI", 12),
            wrap=tk.WORD,
            relief="flat",
            bd=0,
            padx=15,
            pady=15,
            selectbackground=accent_color,
            selectforeground="#1e1e2e",
            insertbackground=text_color,
            highlightthickness=0
        )
        self.translation_label.pack(fill="both", expand=True)
        self.translation_label.config(state="disabled")

        # Footer with status only (no resize button needed!)
        footer_frame = tk.Frame(main_frame, bg=bg_color, height=25)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        # Status indicator
        status_label = tk.Label(
            footer_frame,
            text="Ready",
            bg=bg_color,
            fg="#6c7086",
            font=("Segoe UI", 8),
            anchor="w"
        )
        status_label.pack(side="left", padx=12, pady=4)

        # Create invisible resize areas around the edges
        # Right edge resize area
        right_resize = tk.Frame(main_frame, bg=bg_color, width=8, cursor="sb_h_double_arrow")
        right_resize.pack(side="right", fill="y")
        right_resize.pack_propagate(False)

        # Bottom edge resize area
        bottom_resize = tk.Frame(main_frame, bg=bg_color, height=8, cursor="sb_v_double_arrow")
        bottom_resize.pack(side="bottom", fill="x")
        bottom_resize.pack_propagate(False)

        # Bottom-right corner resize area (diagonal)
        corner_resize = tk.Frame(footer_frame, bg=bg_color, width=20, height=20, cursor="sizing")
        corner_resize.pack(side="right", anchor="se", padx=2, pady=2)

        # Bind resize events to edges and corner
        def bind_resize_events(widget, resize_type):
            widget.bind("<ButtonPress-1>", lambda e: self._start_edge_resize(e, resize_type))
            widget.bind("<ButtonRelease-1>", self._stop_resize)
            widget.bind("<B1-Motion>", lambda e: self._on_edge_resize(e, resize_type))

        bind_resize_events(right_resize, "right")
        bind_resize_events(bottom_resize, "bottom")
        bind_resize_events(corner_resize, "corner")

        # Bind events for dragging
        drag_label.bind("<ButtonPress-1>", self._start_drag)
        drag_label.bind("<ButtonRelease-1>", self._stop_drag)
        drag_label.bind("<B1-Motion>", self._on_drag)

        # Also make the title draggable
        title_label.bind("<ButtonPress-1>", self._start_drag)
        title_label.bind("<ButtonRelease-1>", self._stop_drag)
        title_label.bind("<B1-Motion>", self._on_drag)

        # Store references for smoother resizing
        self.main_frame = main_frame
        self.status_label = status_label

        self.translation_window.focus_set()

        # Add variable to control resize update frequency
        self.last_resize_update = 0
        self.resize_interval = 1/30  # 30 FPS

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
        self.resize_start_width = self.overlay_width
        self.resize_start_height = self.overlay_height
        self.resize_start_pos_x = self.translation_window.winfo_x()
        self.resize_start_pos_y = self.translation_window.winfo_y()

        # Create resize ghost window for smooth feedback
        self.resize_ghost = tk.Toplevel(self.root)
        self.resize_ghost.overrideredirect(True)
        self.resize_ghost.attributes('-alpha', 0.3, '-topmost', True)
        self.resize_ghost.geometry(f"{self.overlay_width}x{self.overlay_height}+{self.resize_start_pos_x}+{self.resize_start_pos_y}")
        self.resize_ghost.config(bg="#89b4fa")  # Blue ghost window

    def _on_resize(self, event):
        """Handles resizing of the overlay window with smoothing"""
        if not hasattr(self, 'resize_ghost') or not self.resize_ghost:
            return

        current_time = time.time()

        # Calculate the new dimensions based on drag distance
        width = max(300, self.resize_start_width + (event.x - self.drag_data["x"]))
        height = max(150, self.resize_start_height + (event.y - self.drag_data["y"]))

        # Update the ghost window for visual feedback at a higher rate
        try:
            self.resize_ghost.geometry(f"{width}x{height}+{self.resize_start_pos_x}+{self.resize_start_pos_y}")
        except tk.TclError:
            # Ghost window might have been destroyed
            return

        # Throttle actual window updates for smoothness
        if current_time - self.last_resize_update >= self.resize_interval:
            # Store new dimensions for when we finish resizing
            self.overlay_width = width
            self.overlay_height = height
            self.last_resize_update = current_time

    def _stop_resize(self, event):
        """Ends resize operation and applies the final size"""
        # Destroy the ghost window
        if hasattr(self, 'resize_ghost') and self.resize_ghost:
            try:
                self.resize_ghost.destroy()
            except tk.TclError:
                pass  # Window already destroyed
            self.resize_ghost = None

        # Apply the final size to the actual window
        if self.translation_window and self.translation_window.winfo_exists():
            self.translation_window.geometry(f"{self.overlay_width}x{self.overlay_height}+{self.translation_window.winfo_x()}+{self.translation_window.winfo_y()}")

        # Reset drag data
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

        # Clean up temporary variables
        if hasattr(self, 'resize_start_width'):
            del self.resize_start_width
            del self.resize_start_height
            del self.resize_start_pos_x
            del self.resize_start_pos_y

        # Update status
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.config(text=f"Resized to {self.overlay_width}x{self.overlay_height}")
            # Reset status after 2 seconds
            self.translation_window.after(2000, lambda: self.status_label.config(text="Ready") if hasattr(self, 'status_label') and self.status_label else None)

    def _start_edge_resize(self, event, resize_type):
        """Begins edge/corner resize operation"""
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.resize_type = resize_type
        self.resize_start_width = self.overlay_width
        self.resize_start_height = self.overlay_height
        self.resize_start_pos_x = self.translation_window.winfo_x()
        self.resize_start_pos_y = self.translation_window.winfo_y()

        # Create resize ghost window for smooth feedback
        self.resize_ghost = tk.Toplevel(self.root)
        self.resize_ghost.overrideredirect(True)
        self.resize_ghost.attributes('-alpha', 0.3, '-topmost', True)
        self.resize_ghost.geometry(f"{self.overlay_width}x{self.overlay_height}+{self.resize_start_pos_x}+{self.resize_start_pos_y}")
        self.resize_ghost.config(bg="#89b4fa")  # Blue ghost window

    def _on_edge_resize(self, event, resize_type):
        """Handles edge/corner resizing with different resize modes"""
        if not hasattr(self, 'resize_ghost') or not self.resize_ghost:
            return

        current_time = time.time()

        # Calculate deltas from start position
        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]

        # Calculate new dimensions based on resize type
        if resize_type == "right":
            # Only width changes
            width = max(300, self.resize_start_width + dx)
            height = self.resize_start_height
        elif resize_type == "bottom":
            # Only height changes
            width = self.resize_start_width
            height = max(150, self.resize_start_height + dy)
        elif resize_type == "corner":
            # Both width and height change (diagonal resize)
            width = max(300, self.resize_start_width + dx)
            height = max(150, self.resize_start_height + dy)
        else:
            return

        # Update the ghost window for visual feedback
        try:
            self.resize_ghost.geometry(f"{width}x{height}+{self.resize_start_pos_x}+{self.resize_start_pos_y}")
        except tk.TclError:
            return

        # Throttle actual window updates for smoothness
        if current_time - self.last_resize_update >= self.resize_interval:
            self.overlay_width = width
            self.overlay_height = height
            self.last_resize_update = current_time

    def _update_translation_display(self, text):
        """Updates the text in the translation overlay window."""
        if not self.translation_window or not self.translation_window.winfo_exists():
            self._create_translation_overlay()

        self.translation_label.config(state="normal")
        self.translation_label.delete(1.0, tk.END)
        self.translation_label.insert(tk.END, text)
        self.translation_label.config(state="disabled")
        self.translation_window.update()
        pyperclip.copy(text)

    def _show_settings(self):
        """Displays the settings window for model selection."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x300")
        self.settings_window.resizable(False, False)
        self.settings_window.attributes('-topmost', True)

        # Center the settings window on screen
        screen_width = self.settings_window.winfo_screenwidth()
        screen_height = self.settings_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        self.settings_window.geometry(f"400x300+{x}+{y}")

        # Modern color scheme (matching control window)
        bg_color = "#1e1e2e"  # Dark background
        accent_color = "#89b4fa"  # Blue accent
        text_color = "#cdd6f4"  # Light text
        button_bg = "#313244"  # Button background
        button_hover = "#45475a"  # Button hover
        input_bg = "#45475a"  # Input background

        self.settings_window.configure(bg=bg_color)

        # Main container with padding
        main_frame = tk.Frame(self.settings_window, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # Header section
        header_frame = tk.Frame(main_frame, bg=bg_color)
        header_frame.pack(fill="x", pady=(0, 20))

        # Settings title
        title_label = tk.Label(
            header_frame,
            text="⚙️ Settings",
            font=("Segoe UI", 18, "bold"),
            fg=accent_color,
            bg=bg_color
        )
        title_label.pack()

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Configure your AI model and preferences",
            font=("Segoe UI", 9),
            fg=text_color,
            bg=bg_color
        )
        subtitle_label.pack(pady=(3, 0))

        # Model selection section
        model_section = tk.Frame(main_frame, bg=bg_color)
        model_section.pack(fill="x", pady=(0, 20))

        # Model label
        model_label = tk.Label(
            model_section,
            text="🤖 Ollama Model:",
            font=("Segoe UI", 11, "bold"),
            fg=text_color,
            bg=bg_color
        )
        model_label.pack(anchor="w", pady=(0, 8))

        # Custom styled dropdown
        self.model_var = StringVar(value=self.current_model)

        # Create a frame for the dropdown with custom styling
        dropdown_frame = tk.Frame(model_section, bg=input_bg, relief="flat", bd=0)
        dropdown_frame.pack(fill="x", pady=(0, 5))

        model_dropdown = OptionMenu(
            dropdown_frame,
            self.model_var,
            *AVAILABLE_MODELS
        )
        model_dropdown.configure(
            bg=input_bg,
            fg=text_color,
            activebackground=button_hover,
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        model_dropdown.pack(fill="x", padx=8, pady=8)

        # Status section
        status_section = tk.Frame(main_frame, bg=bg_color)
        status_section.pack(fill="x", pady=(0, 20))

        # Status label
        status_title_label = tk.Label(
            status_section,
            text="📊 Connection Status:",
            font=("Segoe UI", 11, "bold"),
            fg=text_color,
            bg=bg_color
        )
        status_title_label.pack(anchor="w", pady=(0, 8))

        # Status info frame with background
        status_info_frame = tk.Frame(status_section, bg=input_bg, relief="flat", bd=0)
        status_info_frame.pack(fill="x")

        status_label = tk.Label(
            status_info_frame,
            text="Checking Ollama status...",
            font=("Segoe UI", 9),
            fg=text_color,
            bg=input_bg,
            wraplength=350,
            justify="left"
        )
        status_label.pack(padx=12, pady=10)

        # Check Ollama status
        try:
            models = ollama.list().get('models', [])
            status_text = f"✅ Connected successfully!\nFound {len(models)} available models."
            status_color = "#a6e3a1"  # Green for success
        except Exception as e:
            status_text = f"❌ Connection failed\n{str(e)[:80]}...\n\nPlease ensure Ollama is installed and running."
            status_color = "#f38ba8"  # Red for error

        status_label.config(text=status_text, fg=status_color)

        # Buttons section
        buttons_frame = tk.Frame(main_frame, bg=bg_color)
        buttons_frame.pack(fill="x", pady=(10, 0))

        # Custom button function (reusing from control window)
        def create_settings_button(parent, text, command, primary=False):
            btn_bg = accent_color if primary else button_bg
            btn_hover = "#74c7ec" if primary else button_hover
            btn_text_color = "#1e1e2e" if primary else text_color

            btn_frame = tk.Frame(parent, bg=btn_bg, relief="flat", bd=0)
            btn_frame.pack(side="right", padx=(5, 0))

            inner_frame = tk.Frame(btn_frame, bg=btn_bg)
            inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

            button = tk.Button(
                inner_frame,
                text=text,
                command=command,
                font=("Segoe UI", 10, "bold" if primary else "normal"),
                fg=btn_text_color,
                bg=btn_bg,
                activebackground=btn_hover,
                activeforeground="#ffffff" if not primary else "#1e1e2e",
                relief="flat",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2"
            )
            button.pack(fill="both", expand=True)

            def on_enter(e):
                button.configure(bg=btn_hover)

            def on_leave(e):
                button.configure(bg=btn_bg)

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)

            return btn_frame

        # Cancel button
        create_settings_button(buttons_frame, "Cancel", lambda: self.settings_window.destroy())

        # Save button (primary)
        create_settings_button(buttons_frame, "💾 Save Settings", self._save_settings, primary=True)

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
        self.canvas.pack(fill="both", expand=True)

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
