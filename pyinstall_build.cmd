@echo off
if "%1"=="" (
	echo δָ�����ļ���
) else (
    pyinstaller -F -c -n NewUpdaterTest %1
    echo Build finished!
)
