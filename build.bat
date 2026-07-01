@echo off
pip install -r requirements.txt
pyinstaller --onefile --name photo-coper photo_coper/main.py
echo Build complete. Check dist folder.
pause
