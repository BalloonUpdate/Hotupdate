import json
import os
import random
import subprocess
import sys
import threading
import time
import traceback
from json.decoder import JSONDecodeError

import requests
from PyQt5.QtWidgets import QApplication

from qt import MyMainWindow
from utils.File import File
from workMode.AMode import AMode
from workMode.BMode import BMode


def downloadFile2(url, file, relPath, downloadedBytes, totalKBytes):
    p = relPath
    r = requests.get(url, stream=True)

    if r.status_code != 200:
        text2 = '下载 ' + relPath + ' 时出现了错误,服务器没有按预期返回200:\n'
        text2 += '原始URL: ' + url + '\n'
        text2 += "HTTP CODE: " + str(r.status_code) + '\n'
        mainWindow.es_showMessageBox.emit(text2, '服务器没有按预期返回200')
        mainWindow.es_setShow.emit(False)
        assert False, text2

    totalSize = int(r.headers.get("Content-Length"))
    chunkSize = 1024 * 64
    received = 0

    file.makeParentDirs()
    file.delete()
    f = open(file.path, 'wb+')

    try:
        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            received += len(chunk)

            downloadedBytes[0] += len(chunk)
            mainWindow.es_setProgressValue.emit(int(downloadedBytes[0] / totalKBytes * 1000))

            progress = format(received / totalSize * 100, '.2f') + '% '
            progress2 = "{:.1f}Kb / {:.1f}Kb".format(received / 1024, totalSize / 1024)
            mainWindow.es_setItemText.emit(p, progress + ' ' + progress2 + '  ' + p, False)
            mainWindow.es_setWindowTitle.emit('正在下载新文件 ' + "{:.1f}%".format(downloadedBytes[0] / totalKBytes * 100))

        if received == totalSize:
            mainWindow.es_setItemText.emit(p, '100%  ' + p, True)

    except BaseException as e:
        text3 = '与服务器的连接意外中断:\n'
        text3 += str(e.__repr__()) + '\n'
        mainWindow.es_showMessageBox.emit(text3, '服务器没有按预期返回200')
        mainWindow.es_setShow.emit(False)
        assert False, text3

    if totalSize == 0:
        mainWindow.es_setItemText.emit(p, '100.00% ' + p, True)

    f.close()


def readConfig():
    # 加载配置文件
    settingsFile = File('updater.json')
    settingsFile_mc = File('.minecraft/updater.json')

    if not settingsFile.exists:
        if settingsFile_mc.exists:
            settingsFile = settingsFile_mc
        else:
            msg = '找不到文件 updater.json，请检查以下路径之一: \n' + \
                  settingsFile.path + '\n' + \
                  settingsFile_mc.path
            mainWindow.es_showMessageBox.emit(msg, '错误：无法加载配置文件')
            mainWindow.es_setShow.emit(False)
            assert False, msg

    def checkURL(url: str):
        return url if url.endswith('/') else url + '/'

    return checkURL(json.loads(settingsFile.content)['url'])


def requestMetadata(url: str):
    response = None
    data = None

    try:
        response = requests.get(url)
        data = response.json()
    except requests.exceptions.ConnectionError as e:
        mainWindow.es_showMessageBox.emit(str(e), '请求失败')
        mainWindow.es_setShow.emit(False)
        assert False, '请求失败' + str(e)
    except JSONDecodeError as e:
        text = '访问的URL: ' + response.url + '\n'
        text += 'HTTP CODE: ' + str(response.status_code) + '\n\n'
        text += '原始数据:\n' + response.text[:200] + ('\n...' if len(response.text) > 200 else '')

        mainWindow.es_showMessageBox.emit(text, '服务器返回了无法解码的信息')
        mainWindow.es_setShow.emit(False)
        assert False, '服务器返回了无法解码的信息' + text

    return data


def calculateChanges(mode, rootDir, regexes, regexesMode, structure):
    # 计算要修改的文件
    mainWindow.es_setWindowTitle.emit('正在计算目录')
    mainWindow.es_setProgressVisible.emit(True)  # 打开进度条
    mainWindow.es_setProgressRange.emit(0, 1000)
    mainWindow.es_setProgressValue.emit(1000)
    mainWindow.es_setProgressStatus.emit(1)  # 设置为黄色模式

    if mode:
        workMode = AMode(rootDir.path, regexes, regexesMode)
    else:
        workMode = BMode(rootDir.path, regexes, regexesMode)

    # 开始计算
    workMode.scan(rootDir, structure)

    return workMode


def loadInList(workMode):
    mainWindow.es_setWindowTitle.emit('正在加载列表..')

    for p in workMode.deleteList:
        mainWindow.es_addItem.emit(p, '等待删除 ' + p)

    for p in workMode.downloadList:
        mainWindow.es_addItem.emit(p, '等待下载 ' + p)


def deleteOldFiles(workMode, rootDir):
    mainWindow.es_setProgressStatus.emit(0)
    mainWindow.es_setWindowTitle.emit('正在删除旧文件')

    totalToDelete = len(workMode.deleteList)  # 计算出总共要删除的文件数
    deletedCount = 0
    for p in workMode.deleteList:
        deletedCount += 1
        mainWindow.es_setProgressValue.emit(1000 - int(deletedCount / totalToDelete * 1000))
        mainWindow.es_setItemBold.emit(p, True)
        mainWindow.es_setItemText.emit(p, '已删除: ' + p, True)
        rootDir.append(p).delete()
        time.sleep(0.02 + random.random() * 0.03)


def downloadNewFiles(workMode, rootDir, serverUrl):
    # 计算出总下载量(字节)
    totalKBytes = 0
    for path, length in workMode.downloadMap.items():
        totalKBytes += length

    # 下载新文件
    mainWindow.es_setWindowTitle.emit('正在下载新文件')
    downloadedBytes = [0]

    for p in workMode.downloadList:
        file = rootDir.append(p)
        mainWindow.es_setItemBold.emit(p, True)
        downloadFile2(serverUrl + 'resources/' + p, file, p, downloadedBytes, totalKBytes)


def work():
    try:
        # time.sleep(0.5)

        mainWindow.es_setShow.emit(True)
        mainWindow.es_setWindowTitle.emit('正在连接到服务器..')

        inDevelopment = not getattr(sys, 'frozen', False)

        # 读取配置文件
        serverUrl = readConfig()

        # 获取服务器的文件元数据
        response = requestMetadata(serverUrl)

        mode = response['ModeA']
        regexes = response['Regexes']
        regexesMode = response['MatchAllRegexes']
        structure = response['structure']

        # 更新文件夹的根目录
        rootDir = File('.') if not File('redirect').exists else File('./redirectDir')
        rootDir.mkdirs()

        if rootDir.name == 'redirectDir':
            print('目标文件夹已被重定向到: '+rootDir.path)
        else:
            # 路径检测，以防止误删文件
            if inDevelopment:
                programDir = File(os.path.split(os.path.abspath(sys.argv[0]))[0])
                if programDir.path == File('').path:
                    print('请不要原地执行，请将本程序复制到其它位置后再cd回到这里再执行，否则很容易误删文件')
                    return

        # 计算修改的文件
        workMode = calculateChanges(mode, rootDir, regexes, regexesMode, structure)

        # 加载进列表里
        loadInList(workMode)

        # 删除旧文件
        deleteOldFiles(workMode, rootDir)

        # 下载新文件
        downloadNewFiles(workMode, rootDir, serverUrl)

        # 结束工作
        mainWindow.es_setWindowTitle.emit('没有需要更新的文件')

        # 如果被打包以后就执行一下'RunWhenExit'
        if getattr(sys, 'frozen', False):
            command = response['RunWhenExit']
            if command != '':
                try:
                    subprocess.call(command, shell=True)
                except BaseException as e:
                    text = '要执行的命令: ' + command + '\n'
                    text += str(e.__repr__()) + '\n'
                    mainWindow.es_showMessageBox.emit(text, '执行RunWhenExit时发生了错误')
                    mainWindow.es_setShow.emit(False)
                    return

        time.sleep(1)
        mainWindow.es_setShow.emit(False)

    except BaseException as e:
        if not isinstance(e, AssertionError):
            text = '异常详情: \n'
            text += str(traceback.format_exc())
            mainWindow.es_showMessageBox.emit(text, '发生了未知异常')
            mainWindow.es_setShow.emit(False)
    finally:
        app.quit()
        print('工作线程退出')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MyMainWindow()

    workThread = threading.Thread(target=work, daemon=True)
    workThread.start()

    code = app.exec_()
    sys.exit(code)
