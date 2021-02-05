import subprocess
import sys
import tempfile
import time

import requests

from src.common import inDevelopment
from src.exception.displayable_error import FailedToConnectError, UnexpectedTransmissionError, UnexpectedHttpCodeError
from src.pywebview.updater_web_view import UpdaterWebView
from src.utils.file_comparer import FileComparer
from src.utils.logger import info


class HotUpdateHelper:
    def __init__(self, entry):
        self.workDir = workDir = entry.workDir
        self.e = entry

        self.temporalDir = workDir(tempfile.mkdtemp()) if not inDevelopment else workDir('debug_temp_dir')
        self.temporalDir.mkdirs()
        self.temporalDir.clear()

        self.temporalScript = workDir(tempfile.mkstemp(suffix='.bat')[1]) if not inDevelopment else workDir('debug_temp_script.bat')

        self.hotupdate = workDir(sys.executable).parent if not inDevelopment else workDir('debug_prog_dir')
        self.hotupdate.mkdirs()

    def compare(self, remoteFileStructure: list):
        comparer = FileComparer(self.hotupdate)
        comparer.compareWithList(self.hotupdate, remoteFileStructure)

        # 跳过未知的调试信息(可能是CEFPYTHON生成的，但又没法删除
        exclusions = [
            'debug.log',
            'blob_storage',
            'webrtc_event_logs'
        ]

        for ex in exclusions:
            exFile = self.e.exe.parent(ex)
            exPath = exFile.relPath(self.hotupdate)

            comparer.deleteFiles = [f for f in comparer.deleteFiles if not f.startswith(exPath)]
            comparer.deleteFolders = [f for f in comparer.deleteFolders if not f.startswith(exPath)]

            info('Exclude: ' + exPath)

        return comparer

    def generateBatchStatements(self, comparer: FileComparer):
        # 准备生成用于热替换的batch脚本
        batchText = '''
        @echo off
        echo Preparing..
        
        SET /a count=20
        SET tempFile=.temp.txt
        
        REM waiting utill UpdaterHotupdatePackage.exe exited
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
            file = self.hotupdate[d]
            delCmd = 'del /F /S /Q ' if file.isFile else 'rmdir /S /Q '
            batchText += delCmd + '"' + file.windowsPath + '"\n'
        for d in comparer.deleteFolders:
            file = self.hotupdate[d]
            batchText += f'rmdir /S /Q "{file.windowsPath}"\n'

        # 复制新文件
        source = self.temporalDir.windowsPath + '\\*'
        destination = self.hotupdate.windowsPath + '\\'

        batchText += f'echo Install({len(comparer.downloadFiles)})\n'
        batchText += f'xcopy /E /R /Y "{source}" "{destination}" \n'
        batchText += 'echo Cleanup\n'
        batchText += 'rmdir /S /Q "' + self.temporalDir.windowsPath + '"\n'
        batchText += 'echo done!!\n'
        batchText += 'exit\n'

        # 由启动器来启动，故注释
        # batchText += f'cd /D "{self.e.exe.parent.windowsPath}" && start {self.e.exe.name} \n' if not inDevelopment else 'echo 运行在开发模式\n'

        # batchText += 'del /F /S /Q "' + self.temporalScript.windowsPath + '"'

        return batchText

    def generateStartupCommand(self):
        return f'cd /D "{self.temporalScript.parent.windowsPath}" && start {self.temporalScript.name}'

    def main(self, comparer:FileComparer):
        webview: UpdaterWebView = self.e.webview

        # 生成热更新替换脚本
        batchText = self.generateBatchStatements(comparer)
        startupText = self.generateStartupCommand()

        webview.invokeCallback('upgrading_before_downloading')

        # 创建缺失的目录
        for mf in comparer.downloadFolders:
            self.workDir(mf).mkdirs()

        # 下载新文件
        for path, length in comparer.downloadFiles.items():
            url = self.e.upgradeSource + '/' + path
            file = self.temporalDir(path)

            # 开始下载
            info('downloading: ' + file.name)
            webview.invokeCallback('upgrading_downloading', path, -1, -1)

            try:
                r = requests.get(url, stream=True, timeout=5)
                if r.status_code != 200:
                    raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                received = 0
                chunkSize = 1024 * 64

                file.makeParentDirs()
                with open(file.path, 'xb+') as f:
                    for chunk in r.iter_content(chunk_size=chunkSize):
                        f.write(chunk)
                        received += len(chunk)
                        webview.invokeCallback('upgrading_downloading', path, received, length[0])

            except requests.exceptions.ConnectionError as e:
                raise FailedToConnectError(e, url)
            except requests.exceptions.ChunkedEncodingError as e:
                raise UnexpectedTransmissionError(e, url)

            webview.invokeCallback('upgrading_downloading', path, -2, -2)

        # 将脚本代码写入文件
        with open(self.temporalScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)

        webview.invokeCallback('upgrading_before_installing')

        time.sleep(1)

        # 执行
        subprocess.call(startupText, shell=True)

        # 返回2
        self.e.exitcode = 2

        # temporalDir.delete() # 由批处理文件删除
        # temporalScript.delete() # 由批处理文件删除
