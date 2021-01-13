@echo off

python version.py > temp.txt
set /p filename=< temp.txt

python -c print('%filename%'.split('-')[1]) > temp.txt
set /p version_text=< temp.txt

del temp.txt

del dist\%version_text%
echo Build for %filename%
pyinstaller --noconfirm --version-file version-file.txt --add-data="icon.ico;." -i icon.ico -F -w -n UpdaterHotupdatePackage main.py %1 %2 %3
echo Build finished!

echo %filename% > dist\%version_text%
echo %version_text%


rmdir /S /Q                         D:\nginx-1.19.1\updater-php\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\updater-php\hotupdate\

rmdir /S /Q                         D:\nginx-1.19.1\updater-static\hotupdate\
xcopy /E /R /Y dist\*               D:\nginx-1.19.1\updater-static\hotupdate\

"D:\hyperink\Desktop\NP&Deployer\JsonGenerator-1.0.1.exe" D:\nginx-1.19.1\updater-static\hotupdate
"D:\hyperink\Desktop\NP&Deployer\JsonGenerator-1.0.1.exe" D:\nginx-1.19.1\updater-static\resources