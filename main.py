import json
import random
import subprocess
import sys
import threading
import time
from json.decoder import JSONDecodeError

import requests
from PyQt5.QtWidgets import QApplication

from qt import MyMainWindow
from utils.File import File
from workMode.AMode import AMode
from workMode.BMode import BMode


def checkURL(url: str):
    return url if url.endswith('/') else url + '/'


def work2():
    try:
        work()
    except Exception as e:
        # ts.quit()
        print(e)
        raise e


def work():
    mainWindow.es_setShow.emit(True)
    mainWindow.es_setWindowTitle.emit('正在连接到服务器..')
    time.sleep(0.2)  # 让窗口初始化

    # 加载配置文件
    settingsFile = File('updater.json')

    if not settingsFile.exists:
        sfInMc = settingsFile.parent['.minecraft']['updater.json']
        if not sfInMc.exists:
            msg = '找不到文件 updater.json \n' \
                  '请检查以下路径之一: \n' + \
                  settingsFile.path + '\n' + \
                  sfInMc.path
            mainWindow.es_showMessageBox.emit(msg, '错误：无法加载配置文件')
            mainWindow.es_setShow.emit(False)
            return
        else:
            settingsFile = sfInMc

    settings = json.loads(settingsFile.content)
    settings['url'] = checkURL(settings['url'])

    # 开始更新文件
    response = None

    try:
        response = requests.get(settings['url'])
        infojson = response.json()
    except requests.exceptions.ConnectionError as e:
        mainWindow.es_showMessageBox.emit(str(e), '请求失败')
        mainWindow.es_setShow.emit(False)
        return
    except JSONDecodeError as e:
        text = '访问的URL: '+response.url+'\n'
        text += 'HTTP CODE: '+str(response.status_code)+'\n\n'
        text += '原始数据:\n'+response.text[:200] + ('\n...' if len(response.text) > 200 else '')

        mainWindow.es_showMessageBox.emit(text, '服务器返回了无法解码的信息')
        mainWindow.es_setShow.emit(False)
        return

    # 计算要修改的文件

    mainWindow.es_setWindowTitle.emit('正在计算目录')
    mainWindow.es_setProgressStatus.emit(1)
    mainWindow.es_setProgressVisible.emit(True)
    mainWindow.es_setProgressRange.emit(0, 0)
    mainWindow.es_setProgressValue.emit(0)

    td = File(infojson['RelativePath'])
    td.mkdirs()

    if infojson['Mode'] == 'A':
        hl = AMode(td.absPath, infojson['Regexes'], infojson['RegexesMode'] == "and")
    else:
        hl = BMode(td.absPath, infojson['Regexes'], infojson['RegexesMode'] == "and")

    hl.scan(td, infojson['structure'])

    # print('\n'.join(hl.deleteList))
    # print('----------')
    # print('\n'.join(hl.downloadList))

    mainWindow.es_setWindowTitle.emit('正在加载列表..')
    mainWindow.es_setProgressStatus.emit(2)

    for p in hl.deleteList:
        mainWindow.es_addItem.emit(p, '等待删除: '+p)
        # al.addItem(p, '删除文件 ' + p, 0.0, None)

    for p in hl.downloadList:
        mainWindow.es_addItem.emit(p, '等待下载: '+p)
        # al.addItem(p, '等待下载 ' + p, 0.0, None)

    mainWindow.es_setProgressStatus.emit(0)
    mainWindow.es_setWindowTitle.emit('正在删除旧文件')

    totalKBytes = 0
    for path, length in hl.downloadMap.items():
        totalKBytes += length
    mainWindow.es_setProgressRange.emit(0, 1000)

    totalToDelete = len(hl.deleteList)
    deletedCount = 0
    for p in hl.deleteList:
        print('正在删除文件: '+p)
        deletedCount += 1
        mainWindow.es_setProgressValue.emit(1000 - int(deletedCount / totalToDelete * 1000))
        td.append(p).delete()
        mainWindow.es_setItemText.emit(p, '已删除: '+p, True)
        time.sleep(0.02 + random.random()*0.03)

    def downloadFile2(url: str, file: File, relPath: str, _downloadedBytes):
        r = requests.get(url, stream=True)

        print('正在下载文件: ' + url)

        if r.status_code != 200:
            text2 = '下载 '+relPath+' 时出现了错误,服务器没有按预期返回200:\n'
            text2 += '原始URL: '+url+'\n'
            text2 += "HTTP CODE: " + str(r.status_code) + '\n'
            mainWindow.es_showMessageBox.emit(text2, '服务器没有按预期返回200')
            mainWindow.es_setShow.emit(False)
            assert False, text2

        totalSize = int(r.headers.get("Content-Length"))
        chunkSize = 1024 * 64
        received = 0

        file.makeParentDirs()

        File(file.absPath + '').delete()
        f = open(file.absPath + '', 'xb+')

        try:

            for chunk in r.iter_content(chunk_size=chunkSize):
                f.write(chunk)
                received += len(chunk)

                _downloadedBytes[0] += len(chunk)
                mainWindow.es_setProgressValue.emit(int(_downloadedBytes[0]/totalKBytes*1000))

                progress = format(received / totalSize * 100, '.2f') + '% '
                progress2 = "{:.1f}Kb / {:.1f}Kb".format(received/1024, totalSize/1024)
                mainWindow.es_setItemText.emit(p, progress+' '+p, received == totalSize)
                mainWindow.es_setWindowTitle.emit('正在下载新文件 ' + progress2)

        except BaseException as e:
            text3 = '与服务器的连接意外中断:\n'
            text3 += str(e.__repr__())+'\n'
            mainWindow.es_showMessageBox.emit(text3, '服务器没有按预期返回200')
            mainWindow.es_setShow.emit(False)
            assert False, text3

        if totalSize == 0:

            mainWindow.es_setItemText.emit(p, '100.00% '+p, True)

        f.close()

    mainWindow.es_setWindowTitle.emit('正在下载新文件')

    downloadedBytes = [0]

    for p in hl.downloadList:
        file = td.append(p)
        downloadFile2(settings['url'] + 'resources/' + p, file, p, downloadedBytes)

    mainWindow.es_setWindowTitle.emit('没有需要更新的文件')
    if getattr(sys, 'frozen', False):  # 被打包以后
        command = infojson['RunWhenExit']

        if command != "":
            try:
                subprocess.call(command, shell=True)
            except BaseException as e:
                text = '要执行的命令: '+command+'\n'
                text += str(e.__repr__())+'\n'
                mainWindow.es_showMessageBox.emit(text, '执行RunWhenExit时发生了错误')
                mainWindow.es_setShow.emit(False)
                return

    time.sleep(1)
    mainWindow.es_setShow.emit(False)
    print('工作线程退出')
    app.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MyMainWindow()

    workThread = threading.Thread(target=work2, daemon=True)
    workThread.start()
    # workThread.join()
    code = app.exec_()
    print('主线程退出')
    sys.exit(code)
