#!/bin/bash
echo "🌸 Ariana v2 Setup..."
sudo apt install -y python3-tk python3-venv espeak-ng mpg123 mpv portaudio19-dev 2>/dev/null
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q edge-tts requests SpeechRecognition Pillow mss reportlab python-pptx psutil flask twilio numpy pygame
echo ""
echo "✅ Done! Chalao:"
echo "   source venv/bin/activate && python3 main.py"
