import random
import subprocess
import sys
import time

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

        rootDir = workDir if not inDevelopment else workDir('debug-dir')
        rootDir.mkdirs()

        if inDevelopment:
            info('InDevelopmentMode: ' + rootDir.path)

        # 计算文件差异
        webview.invokeCallback('calculate_differences_for_update')
        work = self.calculateChanges(mode, rootDir, regexes, regexesMode, remoteFilesStructure)

        newFiles = [[filename, length] for filename, length in work.downloadList.items()]
        oldFiles = [file for file in work.deleteList]

        webview.invokeCallback('updating_old_files', oldFiles)
        webview.invokeCallback('updating_new_files', newFiles)

        # 删除旧文件
        webview.invokeCallback('updating_before_removing')

        for path in work.deleteList:
            info('Deleted: '+path)
            webview.invokeCallback('updating_removing', path)
            rootDir(path).delete()
            time.sleep(0.02 + random.random() * 0.03)

        # 下载新文件
        webview.invokeCallback('updating_before_downloading')

        # 开始下载
        for path, length in work.downloadList.items():
            file = rootDir(path)
            url = self.e.updateSource + '/' + path

            info('Downloading: ' + path + ' on ' + url)
            webview.invokeCallback('updating_downloading', path, 0, 0, length)

            r = requests.get(url, stream=True, timeout=5)
            if r.status_code != 200:
                raise UnexpectedHttpCodeError(url, r.status_code, r.text)

            chunkSize = 1024 * 64
            received = 0

            file.makeParentDirs()
            file.delete()
            with open(file.path, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=chunkSize):
                    f.write(chunk)
                    received += len(chunk)
                    webview.invokeCallback('updating_downloading', path, len(chunk), received, length)

        # 如果被打包就执行一下命令
        if getattr(sys, 'frozen', False) and command != '':
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


