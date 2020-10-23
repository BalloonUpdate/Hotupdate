import base64
import json
import os
import random
import subprocess
import sys
import threading
import time
import traceback
from binascii import Error
from json.decoder import JSONDecodeError
from urllib.parse import unquote

import requests
from PyQt5.QtWidgets import QApplication

from qt import MyMainWindow
from utils.File import File
from workMode.AMode import AMode
from workMode.BMode import BMode


def downloadFile2(url, file, relPath, downloadedBytes, totalKBytes, expectantLength):
    p = relPath
    r = requests.get(url, stream=True)

    print('正在下载: ' + p)

    if r.status_code != 200:
        text2 = '下载 ' + relPath + ' 时出现了错误,服务器没有按预期返回200:\n'
        text2 += '原始URL: ' + url + '\n'
        text2 += "HTTP CODE: " + str(r.status_code) + '\n'
        mainWindow.es_showMessageBox.emit(text2, '服务器没有按预期返回200')
        mainWindow.es_close.emit()
        assert False, text2

    includeContentLength = 'Content-Length' in r.headers

    totalSize = int(r.headers.get("Content-Length")) if includeContentLength else expectantLength
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
        mainWindow.es_close.emit()
        assert False, text3

    if totalSize == 0:
        mainWindow.es_setItemText.emit(p, '100.00% ' + p, True)

    f.close()


def findConfigFile():
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
            print(msg)
            mainWindow.es_showMessageBox.emit(msg, '错误：无法加载配置文件')
            mainWindow.es_close.emit()
            assert False, msg

    return settingsFile


def requestMetadata(url: str):
    response = None
    data = None

    try:
        response = requests.get(url)
        data = response.json()
    except requests.exceptions.ConnectionError as e:
        mainWindow.es_showMessageBox.emit(str(e), '请求失败')
        mainWindow.es_close.emit()
        assert False, '请求失败' + str(e)
    except JSONDecodeError as e:
        text = '访问的URL: ' + response.url + '\n'
        text += 'HTTP CODE: ' + str(response.status_code) + '\n\n'
        text += '原始数据:\n' + response.text[:200] + ('\n...' if len(response.text) > 200 else '')

        mainWindow.es_showMessageBox.emit(text, '服务器返回了无法解码的信息')
        mainWindow.es_close.emit()
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
        downloadFile2(serverUrl + 'resources/' + p, file, p, downloadedBytes, totalKBytes, workMode.downloadMap[p])


def work():
    try:
        inDevelopment = not getattr(sys, 'frozen', False)

        # 读取配置文件
        configFile = findConfigFile()
        configObj = json.loads(configFile.content)

        if 'url' in configObj:
            configObj = {
                "URL": configObj['url'],
                "Client": {
                    "VisibleTime": 1500,
                    "Width": 480,
                    "Height": 350
                }
            }

        try:
            serverUrl = unquote(base64.b64decode(configObj['url'] if 'url' in configObj else configObj['URL'], validate=True).decode('utf-8'), 'utf-8')
        except Error:
            serverUrl = configObj['url'] if 'url' in configObj else configObj['URL']

        serverUrl = serverUrl if serverUrl.endswith('/') else serverUrl + '/'
        uiWidth = configObj['Client']['Width']
        uiHeight = configObj['Client']['Height']

        # 初始化窗口
        mainWindow.es_setWindowWidth.emit(uiWidth)
        mainWindow.es_setWindowHeight.emit(uiHeight)
        mainWindow.es_setWindowCenter.emit()  # 居中
        mainWindow.es_setShow.emit(True)
        mainWindow.es_setWindowTitle.emit('正在连接到服务器..')

        # 从服务器获取数据
        response = requestMetadata(serverUrl)

        mode = response['Server']['ModeA']
        regexes = response['Server']['Regexes']
        regexesMode = response['Server']['MatchAllRegexes']
        command = response['Server']['RunWhenExit']
        structure = response['Server']['Structure']
        visibleTime = response['Client']['VisibleTime']
        windowWidth = response['Client']['Width']
        windowHeight = response['Client']['Height']

        # 保存UI数据
        configObj['Client'] = response['Client']
        configFile.content = json.dumps(configObj, ensure_ascii=False, indent=4)

        # 再次设置窗口大小
        mainWindow.es_setWindowWidth.emit(windowWidth)
        mainWindow.es_setWindowHeight.emit(windowHeight)
        mainWindow.es_setWindowCenter.emit()  # 居中

        # 更新文件夹的根目录
        rootDir = File('.') if not File('redirect').exists else File('./redirected-dir')
        rootDir.mkdirs()

        if rootDir.name == 'redirected-dir':
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

        # 如果被打包就执行一下'RunWhenExit'
        if getattr(sys, 'frozen', False) and command != '':
            subprocess.call(command, shell=True)

        if visibleTime >= 0:
            time.sleep(visibleTime / 1000)
            mainWindow.es_close.emit()

    except BaseException as e:
        if not isinstance(e, AssertionError):
            text = '异常详情: \n'
            text += str(traceback.format_exc())
            print(text)
            mainWindow.es_showMessageBox.emit(text, '发生了未知异常')
            mainWindow.es_close.emit()
    finally:
        print('工作线程退出')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MyMainWindow()

    workThread = threading.Thread(target=work, daemon=True)
    workThread.start()

    sys.exit(app.exec_())
