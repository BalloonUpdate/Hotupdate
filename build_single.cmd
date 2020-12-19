@echo off
pyinstaller --noconfirm --version-file version-file.txt -i icon.ico -w -F -n main main.py
echo Build finished!