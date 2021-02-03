import subprocess
import sys
import tempfile
import time

import requests

from src.common import inDevelopment
from src.exception.displayable_error import FailedToConnectError, UnexpectedTransmissionError, UnexpectedHttpCodeError
from src.utils.file import File
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
        return comparer

    def generateBatchStatements(self, comparer: FileComparer):
        # 准备生成用于热替换的batch脚本
        batchText = '''
        @echo off
        echo 准备中..
        
        SET /a count=20
        SET tempFile=.temp.txt
        
        REM 循环检测
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
        batchText += f'echo 删除旧文件({len(comparer.uselessFiles) + len(comparer.uselessFolders)})\n'
        for d in comparer.uselessFiles:
            file = self.hotupdate[d]
            delCmd = 'del /F /S /Q ' if file.isFile else 'rmdir /S /Q '
            batchText += delCmd + '"' + file.windowsPath + '"\n'
        for d in comparer.uselessFolders:
            file = self.hotupdate[d]
            batchText += f'rmdir /S /Q "{file.windowsPath}"\n'

        # 复制新文件
        source = self.temporalDir.windowsPath + '\\*'
        destination = self.hotupdate.windowsPath + '\\'

        batchText += f'echo 复制新文件({len(comparer.missingFiles)})\n'
        batchText += f'xcopy /E /R /Y "{source}" "{destination}" \n'
        batchText += 'echo 清理临时目录\n'
        batchText += 'rmdir /S /Q "' + self.temporalDir.windowsPath + '"\n'
        batchText += 'echo done!!\n'
        batchText += 'exit\n'

        # 由启动器来启动，故注释
        # batchText += f'cd /D "{self.e.exe.parent.windowsPath}" && start {self.e.exe.name} \n' if not inDevelopment else 'echo 运行在开发模式\n'

        # batchText += 'del /F /S /Q "' + self.temporalScript.windowsPath + '"'

        return batchText

    def generateStartupCommand(self):
        return f'cd /D "{self.temporalScript.parent.windowsPath}" && start {self.temporalScript.name}'

    def downloadFile(self, Url: str, file: File, progressCallback, total, downloaded, expectantLength):
        try:
            r = requests.get(Url, stream=True, timeout=5)
            if r.status_code != 200:
                raise UnexpectedHttpCodeError(Url, r.status_code, r.text)

            recv = 0
            includeContentLength = 'Content-Length' in r.headers
            fileSize = int(r.headers.get("Content-Length")) if includeContentLength else expectantLength
            chunkSize = 1024 * 64

            file.makeParentDirs()
            f = open(file.path, 'xb+')

            for chunk in r.iter_content(chunk_size=chunkSize):
                f.write(chunk)
                downloaded += len(chunk)
                recv += len(chunk)
                progressCallback(downloaded, total, recv, fileSize)

            f.close()

            return downloaded
        except requests.exceptions.ConnectionError as e:
            raise FailedToConnectError(e, Url)
        except requests.exceptions.ChunkedEncodingError as e:
            raise UnexpectedTransmissionError(e, Url)

    def main(self, comparer:FileComparer, clientSettings):
        upgradingWindow = self.e.upgradingWindow

        # 生成热更新替换脚本
        batchText = self.generateBatchStatements(comparer)
        startupText = self.generateStartupCommand()

        # 初始化窗口
        upgradingWindow.es_setWindowWidth.emit(clientSettings['width'])
        upgradingWindow.es_setWindowHeight.emit(clientSettings['height'])
        upgradingWindow.es_setShow.emit(True)
        # upgradingWindow.es_setProgressStatus.emit(1)
        # upgradingWindow.es_setProgressStatus.emit(0)

        time.sleep(0.3)
        upgradingWindow.es_setWindowTitle.emit('正在更新文件..')
        upgradingWindow.es_setProgressVisible.emit(True)
        upgradingWindow.es_setProgressRange.emit(0, 1000)
        upgradingWindow.es_setProgressValue.emit(1000)

        # 创建缺失的目录
        for mf in comparer.missingFolders:
            self.workDir(mf).mkdirs()

        # 加载进列表里
        for df in comparer.missingFiles:
            upgradingWindow.es_addItem.emit(df, '等待下载 ' + df)
            time.sleep(0.01)

        # 计算总下载量
        totalKBytes = 0
        downloadedKByte = 0
        for df in comparer.missingFiles.values():
            totalKBytes += df[0]

        # 下载新文件
        for k, v in comparer.missingFiles.items():
            df = k
            url = self.e.upgradeSource + '/' + df
            file = self.temporalDir(df)
            info('downloading: ' + file.name)

            upgradingWindow.es_setItemBold.emit(df, True)

            def progressCallback(recvFileBytes, totalFileBytes, recv, fileSize):
                progress = recvFileBytes / totalFileBytes
                value = int(progress * 1000)
                upgradingWindow.es_setProgressValue.emit(value)
                upgradingWindow.es_setWindowTitle.emit('正在更新 ' + "{:.0f}%".format(progress * 100))

                t1 = format(recv / fileSize * 100, '<4.1f') + '% '
                t2 = "{:<5.1f} Kb / {:<5.1f} Kb".format(recv / 1024, fileSize / 1024)
                upgradingWindow.es_setItemText.emit(df, f'{t1} {df}  ({t2})', False)

                # info(t1 + ' ' + t2 + '  ' + df)

            upgradingWindow.es_setItemText.emit(df, f'100% {df}', True)

            expectantLength = v[0]
            downloadedKByte = self.downloadFile(url, file, progressCallback, totalKBytes, downloadedKByte, expectantLength)
        # 将脚本代码写入文件
        with open(self.temporalScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)

        # 执行
        subprocess.call(startupText, shell=True)

        # 返回2
        self.e.exitcode = 2

        # 关闭窗口
        upgradingWindow.es_close.emit()
        self.e.updatingWindow.es_close.emit()
        # temporalDir.delete() # 由批处理文件删除
        # temporalScript.delete() # 由批处理文件删除
