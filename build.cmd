@echo off
pyinstaller --noconfirm --version-file version-file.txt -w -n main main.py
echo Build finished!
rmdir /S /Q D:\nginx-1.19.1\html\hotupdate\
xcopy /E /R /Y dist\main\* D:\nginx-1.19.1\html\hotupdate\