import ctypes
import subprocess
import sys
import tempfile
import time

import requests
from tqdm import tqdm

from src.common import inDev
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.UnexpectedHttpCodeError import UnexpectedHttpCodeError
from src.exception.UnexpectedTransmissionError import UnexpectedTransmissionError
from src.logging.LoggingSystem import LogSys
from src.utils.file_comparer import FileCompare


class Upgrade:
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
        comparer = FileCompare(self.hotupdateDir)
        comparer.compareWithList(self.hotupdateDir, remoteFileStructure)

        # 跳过未知的调试信息(是CEFPYTHON生成的，但又没法删除
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

            LogSys.if_('Upgrade', 'Exclude: ' + exPath)

        return comparer

    def generateBatchStatements(self, comparer: FileCompare):
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
            ping -n 2 127.0.0.1 > nul 
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

    def downloadFiles(self, comparer: FileCompare):
        # 计算总下载量
        totalKBytes = 0
        downloadedBytes = 0
        for d in comparer.downloadFiles.values():
            totalKBytes += d[0]

        LogSys.is_('Upgrade', '正在下载新的文件，请不要关掉本程序。')

        with tqdm(total=int(totalKBytes / 1024), dynamic_ncols=True, unit='kb', desc='',
                  bar_format="{desc}{percentage:3.1f}% {bar} {n_fmt}/{total_fmt}Kb {rate_fmt}") as pbar:
            downloadedCount = 0

            # 下载新文件
            for path, length in comparer.downloadFiles.items():
                url = self.e.upgradeSource + '/' + path
                file = self.tempDir(path)

                # 开始下载
                LogSys.if_('Upgrade', 'Downloading: ' + file.name)
                LogSys.is_('Upgrade', '下载新版本: ' + file.name)

                downloadedCount += 1
                pbar.set_description(str(downloadedCount) + '/' + str(len(comparer.downloadFiles)))

                try:
                    r = requests.get(url, stream=True, timeout=5)
                    if r.status_code != 200:
                        raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                    # received = 0
                    file.makeParentDirs()
                    with open(file.path, 'xb+') as f:
                        for chunk in r.iter_content(chunk_size=1024 * 64):
                            f.write(chunk)
                            # received += len(chunk)
                            downloadedBytes += len(chunk)
                            pbar.update(int(len(chunk) / 1024))

                except requests.exceptions.ConnectionError as e:
                    raise FailedToConnectError(e, url)
                except requests.exceptions.ChunkedEncodingError as e:
                    raise UnexpectedTransmissionError(e, url)

    def main(self, comparer: FileCompare):
        # 生成升级脚本
        batchText = self.generateBatchStatements(comparer)

        # 下载文件
        self.downloadFiles(comparer)

        # 将脚本写入文件
        with open(self.tempScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)

        # 开始升级
        cmd = f'cd /D "{self.tempScript.parent.windowsPath}" && start {self.tempScript.name}'
        subprocess.call(cmd, shell=True)

        # 返回2
        self.e.exitcode = 2
