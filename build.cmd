@echo off

python ci\generate_version_file.py

python ci\version.py both > temp.txt
set /p filename=< temp.txt

python ci\version.py version > temp.txt
set /p version_text=< temp.txt

del temp.txt

del dist\%version_text%
del dist\%filename%.exe

echo ----------------Build for %filename%----------------
pyinstaller --noconfirm --version-file version-file.txt --add-data="icon.ico;." --add-binary="assets;assets" --add-binary="v4.0.30319;dotnet" -i icon.ico -F -c -n UpdaterHotupdatePackage main.py %1 %2 %3
echo %filename% > dist\%version_text%

echo ----------------Clean up----------------

del /f /s /q version-file.txt
del /f /s /q %filename%.spec
del /f /s /q debug.log

echo ----------------Build %filename% finished!----------------