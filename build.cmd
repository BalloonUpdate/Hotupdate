@echo off
pyinstaller --noconfirm --version-file version-file.txt --add-data="icon.ico;." -i icon.ico -w -n NewUpdater main.py
echo Build finished!
rmdir /S /Q                         D:\nginx-1.19.1\html\hotupdate\
xcopy /E /R /Y dist\NewUpdater\*    D:\nginx-1.19.1\html\hotupdate\
xcopy /E /R /Y extraFiles\*         D:\nginx-1.19.1\html\hotupdate\

rmdir /S /Q                         D:\nginx-1.19.1\updatertest\hotupdate\
xcopy /E /R /Y dist\NewUpdater\*    D:\nginx-1.19.1\updatertest\hotupdate\
xcopy /E /R /Y extraFiles\*         D:\nginx-1.19.1\updatertest\hotupdate\

start D:\hyperink\Desktop\gen.cmd