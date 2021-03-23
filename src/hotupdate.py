import subprocess
import sys
import tempfile
import time

import requests

from src.common import inDev
from src.exception.displayable_error import FailedToConnectError, UnexpectedTransmissionError, UnexpectedHttpCodeError
from src.pywebview.updater_web_view import UpdaterWebView
from src.utils.file_comparer import FileComparer
from src.utils.logger import info


class HotUpdateHelper:
    def __init__(self, entry):
        self.workDir = workDir = entry.workDir
        self.e = entry

        # 创建一个临时目录用来存放下载缓存
        self.tempDir = workDir(tempfile.mkdtemp()) if not inDev else workDir('temp_dir')
        self.tempDir.mkdirs()
        self.tempDir.clear()

        # 临时文件用来存放升级脚本
        self.tempScript = workDir(tempfile.mkstemp(suffix='.bat')[1]) if not inDev else workDir('temp_script.bat')

        self.hotupdateDir = workDir(sys.executable).parent if not inDev else workDir('program')
        self.hotupdateDir.mkdirs()

    def compare(self, remoteFileStructure: list):
        comparer = FileComparer(self.hotupdateDir)
        comparer.compareWithList(self.hotupdateDir, remoteFileStructure)

        # 跳过未知的调试信息(可能是CEFPYTHON生成的，但又没法删除
        exclusions = [
            'debug.log',
            'blob_storage',
            'webrtc_event_logs'
        ]

        for ex in exclusions:
            exFile = self.e.exe.parent(ex)
            exPath = exFile.relPath(self.hotupdateDir)

            comparer.deleteFiles = [f for f in comparer.deleteFiles if not f.startswith(exPath)]
            comparer.deleteFolders = [f for f in comparer.deleteFolders if not f.startswith(exPath)]

            info('Exclude: ' + exPath)

        return comparer

    def generateBatchStatements(self, comparer: FileComparer):
        # 升级脚本
        batchText = '''
        @echo off
        echo Preparing..
        
        SET /a count=20
        SET tempFile=.temp.txt
        
        REM waiting until UpdaterHotupdatePackage.exe exited
        :check
        tasklist.exe | findstr UpdaterHotupdatePackage.exe > %tempFile%
        set /p Running=<%tempFile%
        
        if %count% LSS 0 ( exit )
        set /a count=%count%-1
        
        if "%Running%" NEQ "" (
            ping -n 1 127.0.0.1 > nul 
            set Running=
            goto check
        )
        
        REM del %tempFile%
        '''

        # 删除旧文件
        batchText += f'echo Remove({len(comparer.deleteFiles) + len(comparer.deleteFolders)})\n'
        for d in comparer.deleteFiles:
            file = self.hotupdateDir[d]
            delCmd = 'del /F /S /Q ' if file.isFile else 'rmdir /S /Q '
            batchText += delCmd + '"' + file.windowsPath + '"\n'
        for d in comparer.deleteFolders:
            file = self.hotupdateDir[d]
            batchText += f'rmdir /S /Q "{file.windowsPath}"\n'

        # 复制新文件
        source = self.tempDir.windowsPath + '\\*'
        destination = self.hotupdateDir.windowsPath + '\\'

        batchText += f'echo Install({len(comparer.downloadFiles)})\n'
        batchText += f'xcopy /E /R /Y "{source}" "{destination}"\n'
        batchText += 'echo Cleanup\n'
        batchText += f'rmdir /S /Q "{self.tempDir.windowsPath}"\n'
        batchText += 'exit'
        return batchText

    def downloadFiles(self, comparer: FileComparer):
        webview: UpdaterWebView = self.e.webview

        # 下载新文件
        for path, length in comparer.downloadFiles.items():
            url = self.e.upgradeSource + '/' + path
            file = self.tempDir(path)

            # 开始下载
            info('Downloading: ' + file.name)
            webview.invokeCallback('upgrading_downloading', path, 0, 0, length[0])

            try:
                r = requests.get(url, stream=True, timeout=5)
                if r.status_code != 200:
                    raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                received = 0
                file.makeParentDirs()
                with open(file.path, 'xb+') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 64):
                        f.write(chunk)
                        received += len(chunk)
                        webview.invokeCallback('upgrading_downloading', path, len(chunk), received, length[0])

            except requests.exceptions.ConnectionError as e:
                raise FailedToConnectError(e, url)
            except requests.exceptions.ChunkedEncodingError as e:
                raise UnexpectedTransmissionError(e, url)

    def main(self, comparer: FileComparer):
        webview: UpdaterWebView = self.e.webview

        # 生成升级脚本
        batchText = self.generateBatchStatements(comparer)

        webview.invokeCallback('upgrading_before_downloading')

        # 下载文件
        self.downloadFiles(comparer)

        # 将脚本写入文件
        with open(self.tempScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)

        webview.invokeCallback('upgrading_before_installing')

        time.sleep(1)

        # 开始升级
        cmd = 'cd /D "{self.tempScript.parent.windowsPath}" && start {self.tempScript.name}'
        subprocess.call(cmd, shell=True)

        # 返回2
        self.e.exitcode = 2
