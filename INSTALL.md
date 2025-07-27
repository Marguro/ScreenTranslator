# Screen Translator - Installation Guide

## ความต้องการของระบบ

### 1. Python (3.8 หรือใหม่กว่า)
- Windows: ดาวน์โหลดจาก https://python.org
- Linux: `sudo apt install python3 python3-pip`
- macOS: `brew install python`

### 2. Tesseract OCR
**Windows:**
- ดาวน์โหลดจาก: https://github.com/UB-Mannheim/tesseract/wiki
- ติดตั้งที่ตำแหน่งเริ่มต้น: `C:\Program Files\Tesseract-OCR\`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

### 3. Ollama AI
- ดาวน์โหลดและติดตั้งจาก: https://ollama.ai
- ติดตั้งโมเดล AI:
```bash
ollama pull gemma3n
ollama pull phi3:mini
```

## การติดตั้งโปรแกรม

### 1. Clone หรือดาวน์โหลดโปรเจค
```bash
git clone <repository-url>
cd ScreenTranslator
```

### 2. ติดตั้ง Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. เรียกใช้โปรแกรม
```bash
python ScreenTranslator.py
```

## การแก้ปัญหา

### ปัญหา Tesseract ไม่เจอ
- ตรวจสอบว่าติดตั้ง Tesseract แล้ว
- ใน Linux/macOS: ตรวจสอบด้วย `which tesseract`
- ในระบบใหม่โปรแกรมจะหาเส้นทาง Tesseract อัตโนมัติ

### ปัญหา Ollama
- ตรวจสอบว่า Ollama ทำงานอยู่: `ollama list`
- เริ่มต้น Ollama service ถ้าจำเป็น

### ปัญหาสิทธิ์
- Linux/macOS: อาจต้องใช้ `sudo` สำหรับการจับภาพหน้าจอ
- Windows: เรียกใช้ Command Prompt แบบ Administrator

## การใช้งาน

1. เปิดโปรแกรม: `python ScreenTranslator.py`
2. กด Alt สองครั้งเร็วๆ หรือคลิก "📱 Capture Screen Area"
3. เลือกพื้นที่ที่ต้องการแปล
4. รอการแปลและคัดลอกผลลัพธ์

## การตั้งค่า

- การตั้งค่าจะถูกบันทึกอัตโนมัติใน:
  - Windows: `C:\Users\[username]\.screen_translator_settings.json`
  - Linux/macOS: `~/.screen_translator_settings.json`
