import random
import subprocess
import sys
import time

import requests

from src.newupdater.common import inDevelopment
from src.newupdater.exception.displayable_error import UnexpectedHttpCodeError
from src.newupdater.utils.logger import info
from src.newupdater.work_mode.mode_a import AMode
from src.newupdater.work_mode.mode_b import BMode


class NewUpdater:
    def __init__(self, entry):
        self.e = entry

    def main(self, response1, clientSettings):
        updatingWindow = self.e.updatingWindow
        workDir = self.e.workDir

        windowWidth = clientSettings['width']
        windowHeight = clientSettings['height']
        visibleTime = clientSettings['visible_time']

        updatingInfo = response1['server']
        mode = updatingInfo['mode_a']
        regexes = updatingInfo['regexes']
        regexesMode = updatingInfo['match_all_regexes']
        command = updatingInfo['command_before_exit']

        info(f'ModeA: {mode}')
        info(f'Regexes: {regexes}')
        info(f'RegexesMode: {regexesMode}')
        info(f'Command: {command}')

        # 检查最新版本
        response3 = self.e.httpGetRequest(self.e.updateApi)
        remoteFilesStructure = response3

        # 初始化窗口
        updatingWindow.es_setWindowWidth.emit(windowWidth)
        updatingWindow.es_setWindowHeight.emit(windowHeight)
        updatingWindow.es_setWindowCenter.emit()
        updatingWindow.es_setShow.emit(True)
        time.sleep(0.3)

        rootDir = workDir if not inDevelopment else workDir('debugging-dir')
        rootDir.mkdirs()

        if inDevelopment:
            info('文件夹已被重定向到: ' + rootDir.path)

        # 计算要修改的文件
        work = self.calculateChanges(mode, rootDir, regexes, regexesMode, remoteFilesStructure)

        # 加载进列表里
        updatingWindow.es_setWindowTitle.emit('正在加载列表..')
        for df in work.deleteList:
            updatingWindow.es_addItem.emit(df, '等待删除 ' + df)
        for df in work.downloadList:
            updatingWindow.es_addItem.emit(df, '等待下载 ' + df)

        # 删除旧文件
        updatingWindow.es_setProgressStatus.emit(0)  # 绿色
        updatingWindow.es_setWindowTitle.emit('正在删除旧文件..')
        totalToDelete = len(work.deleteList)  # 计算出总共要删除的文件数
        deletedCount = 0
        for df in work.deleteList:
            deletedCount += 1
            updatingWindow.es_setProgressValue.emit(1000 - int(deletedCount / totalToDelete * 1000))
            updatingWindow.es_setItemBold.emit(df, True)
            updatingWindow.es_setItemText.emit(df, '已删除: ' + df, True)
            info('正在删除文件: '+df)
            rootDir(df).delete()
            time.sleep(0.02 + random.random() * 0.03)

        # 下载新文件
        updatingWindow.es_setWindowTitle.emit('正在下载新文件..')
        totalKBytes = 0  # 计算出总下载量(字节)
        for length in work.downloadMap.values():
            totalKBytes += length

        # 开始下载
        downloadedBytes = 0
        for df in work.downloadList:
            file = rootDir(df)
            updatingWindow.es_setItemBold.emit(df, True)
            downloadedBytes = self.downloadFile(self.e.updateSource+'/'+df, file, df, downloadedBytes, totalKBytes, work.downloadMap[df])

        updatingWindow.es_setWindowTitle.emit('所有文件已是最新')

        # 如果被打包就执行一下命令
        if getattr(sys, 'frozen', False) and command != '':
            subprocess.call(f'cd /D "{self.e.exe.parent.parent.parent.windowsPath}" && {command}', shell=True)

        if visibleTime >= 0:
            time.sleep(visibleTime / 1000)
            updatingWindow.es_close.emit()

        updatingWindow.es_close.emit()
        self.e.upgradingWindow.es_close.emit()

        info('工作线程退出')

    def calculateChanges(self, mode, rootDir, regexes, regexesMode, structure):
        """计算要修改的文件"""

        updatingWindow = self.e.updatingWindow

        updatingWindow.es_setWindowTitle.emit('正在计算目录..')
        updatingWindow.es_setProgressVisible.emit(True)
        updatingWindow.es_setProgressRange.emit(0, 1000)
        updatingWindow.es_setProgressValue.emit(1000)
        updatingWindow.es_setProgressStatus.emit(1)  # 黄色

        if mode:
            workMode = AMode(rootDir, regexes, regexesMode)
        else:
            workMode = BMode(rootDir, regexes, regexesMode)

        workMode.scan(rootDir, structure)
        return workMode

    def downloadFile(self, url, file, filePath, downloadedBytes, totalKBytes, expectantLength):
        updatingWindow = self.e.updatingWindow
        r = requests.get(url, stream=True, timeout=3)

        info('正在下载: ' + filePath+' on '+url)

        if r.status_code != 200:
            if r.status_code != 200:
                raise UnexpectedHttpCodeError(url, r.status_code, r.text)

        includeContentLength = 'Content-Length' in r.headers
        totalSize = int(r.headers.get("Content-Length")) if includeContentLength else expectantLength
        chunkSize = 1024 * 64
        received = 0

        file.makeParentDirs()
        file.delete()
        f = open(file.path, 'wb+')

        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            received += len(chunk)

            downloadedBytes += len(chunk)
            updatingWindow.es_setProgressValue.emit(int(downloadedBytes / totalKBytes * 1000))

            t1 = format(received / totalSize * 100, '.1f') + '% '
            t2 = "{:.1f}Kb / {:.1f}Kb".format(received / 1024, totalSize / 1024)
            updatingWindow.es_setItemText.emit(filePath, t1 + ' ' + t2 + '  ' + filePath, False)
            updatingWindow.es_setWindowTitle.emit('正在下载新文件 ' + "{:.1f}%".format(downloadedBytes / totalKBytes * 100))

        if received == totalSize:
            updatingWindow.es_setItemText.emit(filePath, '100%  ' + filePath, True)

        if totalSize == 0:
            updatingWindow.es_setItemText.emit(filePath, '100%  ' + filePath, True)

        f.close()

        return downloadedBytes
