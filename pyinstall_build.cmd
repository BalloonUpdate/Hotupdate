@echo off
pyinstaller -F -c -n loader.exe loader.py
pyinstaller -F -w -n main.exe main.py
echo Build finished!

