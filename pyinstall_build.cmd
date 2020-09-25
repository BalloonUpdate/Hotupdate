@echo off
pyinstaller -F -c -n updater.exe loader.py
pyinstaller -F -w -n main main.py
echo Build finished!

