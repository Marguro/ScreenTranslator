from PyQt6.QtCore import QThread, pyqtSignal
import ollama
from src.config import Config

class TranslationWorker(QThread):
    """Background thread for translation to keep UI responsive"""
    translation_finished = pyqtSignal(str)

    def __init__(self, text: str, model: str):
        super().__init__()
        self.text = text
        self.model = model

    def run(self):
        """Run the translation process in the background"""
        try:
            prompt = (
                f'Translate English to Thai, only provide Thai translation:\n'
                f"Provide ONLY the Thai translation, NOTHING ELSE. Do NOT explain or add any other text.\n"
                f'"{self.text}"\n\nThai Translation:'
            )

            model_options = Config.get_model_options(self.model)
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options=model_options
            )

            translated_text = response['response'].strip()

            # Validate Thai characters
            if not any('\u0e00' <= char <= '\u0e7f' for char in translated_text):
                result = f"Translation Error: ตัวอักษรไม่ถูกต้อง\n\nOriginal response: {translated_text}"
            else:
                result = translated_text

        except Exception as e:
            result = f"Translation Error: {e}"

        # noinspection PyUnresolvedReferences
        self.translation_finished.emit(result)