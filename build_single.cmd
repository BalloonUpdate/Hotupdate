@echo off
pyinstaller --noconfirm --version-file version-file.txt -w -F -n main main.py
echo Build finished!