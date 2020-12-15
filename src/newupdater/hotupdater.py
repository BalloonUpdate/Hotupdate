import subprocess
import sys
import tempfile
import time

import requests

from src.newupdater.common import inDevelopment
from src.newupdater.exception.displayable_error import FailedToConnectError, UnexpectedTransmissionError, UnexpectedHttpCodeError
from src.newupdater.hotupdate.file_comparer import FileComparer
from src.newupdater.utils.file import File
from src.newupdater.utils.logger import info


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
        comparer.compare(self.hotupdate, remoteFileStructure)
        return comparer

    def generateBatchStatements(self, comparer: FileComparer):
        # 准备生成用于热替换的batch脚本
        batchText = '@echo off \n'
        batchText += 'echo 准备中.. \n'
        batchText += 'ping -n 2 127.0.0.1 > nul \n'

        # 删除旧文件
        batchText += f'echo 删除旧文件({len(comparer.deleteList)})\n'
        for d in comparer.deleteList:
            file = self.hotupdate[d]
            delCmd = 'del /F /S /Q ' if file.isFile else 'rmdir /S /Q '
            batchText += delCmd + '"' + file.windowsPath + '"\n'

        # 复制新文件
        source = self.temporalDir.windowsPath + '\\*'
        destination = self.hotupdate.windowsPath + '\\'

        batchText += f'echo 复制新文件({len(comparer.downloadList)})\n'
        batchText += f'xcopy /E /R /Y "{source}" "{destination}" \n'
        batchText += 'echo 清理临时目录\n'
        batchText += 'ping -n 1 127.0.0.1 > nul \n'
        batchText += 'rmdir /S /Q "' + self.temporalDir.windowsPath + '"\n'
        batchText += 'echo done!!\n'
        batchText += 'ping -n 2 127.0.0.1 > nul \n'
        batchText += f'cd /D "{self.e.exe.parent.windowsPath}" && start {self.e.exe.name} \n' if not inDevelopment else 'echo 运行在开发模式\n'
        batchText += 'exit\n'
        batchText += 'del /F /S /Q "' + self.temporalScript.windowsPath + '"'

        return batchText

    def generateStartupCommand(self):
        return f'cd /D "{self.temporalScript.parent.windowsPath}" && start {self.temporalScript.name}'

    def downloadFile(self, Url: str, file: File, progressCallback, total, downloaded, expectantLength):
        try:
            r = requests.get(Url, stream=True)
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

    def main(self, comparer: FileComparer):
        upgradingWindow = self.e.upgradingWindow

        # 生成热更新替换脚本
        batchText = self.generateBatchStatements(comparer)
        startupText = self.generateStartupCommand()

        # 准备下载新文件
        upgradingWindow.es_setShow.emit(True)
        # upgradingWindow.es_setProgressStatus.emit(1)
        # upgradingWindow.es_setProgressStatus.emit(0)

        time.sleep(0.3)
        upgradingWindow.es_setWindowTitle.emit('正在更新文件..')
        upgradingWindow.es_setProgressVisible.emit(True)
        upgradingWindow.es_setProgressRange.emit(0, 1000)
        upgradingWindow.es_setProgressValue.emit(1000)

        # 加载进列表里
        for df in comparer.downloadList:
            upgradingWindow.es_addItem.emit(df, '等待下载 ' + df)

        # 计算总下载量
        totalKBytes = 0
        downloadedKByte = 0
        for df in comparer.downloadMap.values():
            totalKBytes += df

        # 下载新文件
        for df in comparer.downloadList:
            url = self.e.upgradeSource + '/' + df
            file = self.temporalDir(df)
            info('下载: ' + file.name)

            upgradingWindow.es_setItemBold.emit(df, True)

            def progressCallback(recvFileBytes, totalFileBytes, recv, fileSize):
                progress = recvFileBytes / totalFileBytes
                value = int(progress * 1000)
                upgradingWindow.es_setProgressValue.emit(value)
                upgradingWindow.es_setWindowTitle.emit('正在更新 ' + "{:.1f}%".format(progress * 100))

                t1 = format(recv / fileSize * 100, '.1f') + '% '
                t2 = "{:.1f}Kb / {:.1f}Kb".format(recv / 1024, fileSize / 1024)
                upgradingWindow.es_setItemText.emit(df, t1 + ' ' + t2 + '  ' + df, True)

                # info(t1 + ' ' + t2 + '  ' + df)

            expectantLength = comparer.downloadMap[df]
            downloadedKByte = self.downloadFile(url, file, progressCallback, totalKBytes, downloadedKByte, expectantLength)
        # 将脚本代码写入文件
        with open(self.temporalScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)
        # 执行
        subprocess.call(startupText, shell=True)

        upgradingWindow.es_close.emit()
        self.e.updatingWindow.es_close.emit()

        # sys.exit()

        # temporalDir.delete() # 由批处理文件删除
        # temporalScript.delete() # 由批处理文件删除
