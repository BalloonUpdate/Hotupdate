@echo off
pyinstaller -F -n main main.py
echo Build finished!
copy /Y dist\main.exe D:\nginx-1.19.1\html\hotupdate-.bin