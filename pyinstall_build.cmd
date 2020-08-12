@echo off
if "%1"=="" (
	echo main file is not given!
) else (
    pyinstaller -F -c -n %2 %1
    echo Build finished!
)
