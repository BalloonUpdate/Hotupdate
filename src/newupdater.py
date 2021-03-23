import random
import subprocess
import sys
import time
from multiprocessing.pool import ThreadPool
from queue import Queue

import requests

from src.common import inDevelopment
from src.exception.displayable_error import UnexpectedHttpCodeError
from src.pywebview.updater_web_view import UpdaterWebView
from src.utils.logger import info
from src.work_mode.mode_a import AMode
from src.work_mode.mode_b import BMode


class NewUpdater:
    def __init__(self, entry):
        self.e = entry

    def main(self, response1, settingsJson):
        workDir = self.e.workDir
        webview: UpdaterWebView = self.e.webview

        re = response1['server']
        mode = re['mode_a']
        regexes = re['regexes']
        regexesMode = re['match_all_regexes']
        command = re['command_before_exit']

        info(f'ModeA: {mode}')
        info(f'Regexes: {regexes}')
        info(f'RegexesMode: {regexesMode}')
        info(f'Command: {command}')

        # 检查最新版本
        webview.invokeCallback('check_for_update', self.e.updateApi)
        remoteFilesStructure = self.e.httpGetRequest(self.e.updateApi)

        rootDir = workDir if not inDevelopment else workDir('download')
        rootDir.mkdirs()

        if inDevelopment:
            info('InDevelopmentMode: ' + rootDir.path)

        # 计算文件差异
        webview.invokeCallback('calculate_differences_for_update')
        work = self.calculateChanges(mode, rootDir, regexes, regexesMode, remoteFilesStructure)

        newFiles = [[filename, length] for filename, length in work.downloadList.items()]
        oldFiles = [file for file in work.deleteList]

        # webview.invokeCallback('updating_old_files', oldFiles)
        webview.invokeCallback('updating_new_files', newFiles)

        # 删除旧文件
        webview.invokeCallback('updating_before_removing')

        for path in work.deleteList:
            info('Deleted: ' + path)
            # webview.invokeCallback('updating_removing', path)
            rootDir(path).delete()
            # time.sleep(0.01)

        # 下载新文件
        webview.invokeCallback('updating_before_downloading')

        maxParallel = self.e.getSettingsJson()['parallel'] if 'parallel' in self.e.getSettingsJson() else 1
        chunkSize = self.e.getSettingsJson()['chunk_size'] if 'chunk_size' in self.e.getSettingsJson() else 32
        autoChunkSize = 'chunk_size' not in self.e.getSettingsJson()

        downloadQueue = Queue(1000000)
        threadPool = ThreadPool(maxParallel)

        print('Count of downloadTask: ' + str(len(work.downloadList.items())))

        # 开始下载
        for path, length in work.downloadList.items():
            _file = rootDir(path)
            _url = self.e.updateSource + '/' + path
            downloadQueue.put([_file, _url, path, length])

        def downloadTask():
            while not downloadQueue.empty():
                task = downloadQueue.get(timeout=10)
                file = task[0]
                url = task[1]
                path = task[2]
                length = task[3]

                info('Downloading: ' + path + ' from ' + url)
                webview.invokeCallback('updating_downloading', path, 0, 0, length)

                r = requests.get(url, stream=True, timeout=5)
                if r.status_code != 200:
                    raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                if autoChunkSize:
                    cs = int(length / 1024 / 1)
                    _cs = max(4, min(1024, cs))
                    _chunkSize = 1024 * _cs
                    info('AutoChunkSize: File: '+path+'  len: '+str(length) + '  chunk: '+str(_cs)+' of '+str(cs))
                else:
                    _chunkSize = 1024 * chunkSize
                received = 0

                file.makeParentDirs()
                file.delete()
                with open(file.path, 'wb+') as f:
                    for chunk in r.iter_content(chunk_size=_chunkSize):
                        f.write(chunk)
                        received += len(chunk)
                        webview.invokeCallback('updating_downloading', path, len(chunk), received, length)

        for i in range(0, maxParallel):
            threadPool.apply_async(downloadTask)

        threadPool.close()
        threadPool.join()

        # 如果被打包就执行一下命令
        if inDevelopment and command != '':
            subprocess.call(f'cd /D "{self.e.exe.parent.parent.parent.windowsPath}" && {command}', shell=True)

        webview.invokeCallback('cleanup')

        if settingsJson['visible_time'] >= 0:
            time.sleep(settingsJson['visible_time'] / 1000)

        info('Webview Cleanup')

    @staticmethod
    def calculateChanges(mode, rootDir, regexes, regexesMode, structure):
        """计算要修改的文件"""

        if mode:
            workMode = AMode(rootDir, regexes, regexesMode)
        else:
            workMode = BMode(rootDir, regexes, regexesMode)

        workMode.scan(rootDir, structure)

        return workMode
