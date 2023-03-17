@echo off
pip install -r requirements.txt
pip install -U openai-whisper
pip3 uninstall torch
pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116