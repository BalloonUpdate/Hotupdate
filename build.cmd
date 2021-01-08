@echo off

python version.py > temp.txt
set /p filename=< temp.txt
del temp.txt

echo Build for %filename%

pyinstaller --noconfirm --version-file version-file.txt --add-data="icon.ico;." -i icon.ico -F -w -n NewUpdater main.py %1 %2 %3
echo Build finished!
rmdir /S /Q                         D:\nginx-1.19.1\html\hotupdate\
REM xcopy /E /R /Y dist\%filename%\*    D:\nginx-1.19.1\html\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\html\hotupdate\


rmdir /S /Q                         D:\nginx-1.19.1\updatertest\hotupdate\
REM xcopy /E /R /Y dist\%filename%\*    D:\nginx-1.19.1\updatertest\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\updatertest\hotupdate\

D:\hyperink\Desktop\JsonGenerator-1.0.1.exe D:\nginx-1.19.1\updatertest\hotupdate
D:\hyperink\Desktop\JsonGenerator-1.0.1.exe D:\nginx-1.19.1\updatertest\resources