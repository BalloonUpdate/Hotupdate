@echo off

python version.py > temp.txt
set /p filename=< temp.txt
del temp.txt

echo Build for %filename%

pyinstaller --noconfirm --version-file version-file.txt --add-data="icon.ico;." -i icon.ico -F -w -n UpdaterHotupdatePackage main.py %1 %2 %3
echo Build finished!

rmdir /S /Q                         D:\nginx-1.19.1\updater-php\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\updater-php\hotupdate\

rmdir /S /Q                         D:\nginx-1.19.1\updater-static\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\updater-static\hotupdate\

"D:\hyperink\Desktop\NP&Deployer\JsonGenerator-1.0.1.exe" D:\nginx-1.19.1\updater-static\hotupdate
"D:\hyperink\Desktop\NP&Deployer\JsonGenerator-1.0.1.exe" D:\nginx-1.19.1\updater-static\resources