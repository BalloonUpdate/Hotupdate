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
REM copy ci\fix\hook-cefpython3.py venv\Lib\site-packages\PyInstaller\hooks
pyinstaller --noconfirm --version-file version-file.txt --add-binary="icon.ico;." --add-binary="build-info.json;." --add-binary="assets;assets" --add-binary="v4.0.30319;dotnet" -i icon.ico -F -c -n UpdaterHotupdatePackage main.py %1 %2 %3
echo %filename% > dist\%version_text%

echo ----------------Clean up----------------

del /f /s /q version-file.txt
del /f /s /q build-info.json
del /f /s /q %filename%.spec
del /f /s /q debug.log

echo ----------------Build %filename% finished!----------------