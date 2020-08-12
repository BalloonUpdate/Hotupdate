@echo off
if "%1"=="" (
	echo 未指定主文件名
) else (
    pyinstaller -F -c -n NewUpdaterTest %1
    echo Build finished!
)
