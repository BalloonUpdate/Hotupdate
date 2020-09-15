import json
import platform
import random
import subprocess
import sys
import threading
import time
from json.decoder import JSONDecodeError

import requests

from CursesLib.Terminal import Terminal
from CursesLib.utils.ChineseSpace import smartStretch
from CursesLib.window.DialogWindow import DialogWindow
from CursesLib.window.ProcessListWindow import ProcessListWindow
from CursesLib.window.component.CloseButton import CloseButton
from CursesLib.window.component.WindowTitle import WindowTitle
from File import File
from terminal import setFont, setBuffer
from work.BMode import BMode
from work.AMode import AMode


def checkURL(url: str):
    return url if url.endswith('/') else url + '/'


class AList(ProcessListWindow):
    def __init__(self):
        super().__init__()

        if not platform.platform().startswith('Windows-10'):
            border = self.getComponent('border')
            border.enable = False
            # border.bgChar = curses.ACS_VLINE
            border.markChar = '|'

        self.addComponent("title", WindowTitle(smartStretch('更新列表')))
        self.addComponent("close", CloseButton())


def work2():
    try:
        work()
    except Exception as e:
        ts.quit()
        print(e)
        raise e


def work():
    # 加载配置文件
    settingsFile = File('updater.json')

    if not settingsFile.exists:
        sfInMc = settingsFile.parent['.minecraft']['updater.json']
        if not sfInMc.exists:
            msg = '找不到文件 updater.json \n' \
                  '请检查以下路径之一: \n' + \
                  settingsFile.path + '\n' + \
                  sfInMc.path
            ts.addWindow(DialogWindow(msg, lambda: exit(), '错误:无法加载配置文件'))
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
        ts.addWindow(DialogWindow('请求失败,连接错误: \n'+str(e), lambda: exit()))
        return
    except JSONDecodeError as e:
        text = '服务器返回了无法解码的信息:\n'
        text += '访问的URL: '+response.url+'\n'
        text += 'HTTP CODE: '+str(response.status_code)+'\n\n'
        text += '原始数据:\n'+response.text
        ts.addWindow(DialogWindow(text, lambda: exit()))
        return

    # 计算要修改的文件
    al.getComponent('title').title = smartStretch('正在计算目录')

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

    for p in hl.deleteList:
        al.addItem(p, '删除文件 ' + p, 0.0, None)

    for p in hl.downloadList:
        al.addItem(p, '等待下载 ' + p, 0.0, None)

    al.getComponent('title').title = smartStretch('正在下载新的文件 ')

    if al.hiddenLines != 0:
        al.getComponent('title').title += smartStretch(' (鼠标滚轮可以滑动列表)')

    for p in hl.deleteList:
        td.append(p).delete()
        # al.removeItem(p)
        al.getItem(p)[2] = -1

        if al.viewFollow:
            al.lookAtItem(p)
        else:
            al.drawAFrame()
        time.sleep(0.03 + random.random()*0.05)

    def downloadFile2(url: str, file: File, relPath: str):
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            text2 = '下载 '+relPath+' 时出现了错误,服务器没有按预期返回200:\n'
            text2 += '原始URL: '+url+'\n'
            text2 += "HTTP CODE: " + str(r.status_code) + '\n'
            ts.addWindow(DialogWindow(text2, lambda: exit()))
            raise AssertionError

        totalSize = int(r.headers.get("Content-Length"))
        chunkSize = 1024
        received = 0

        file.makeParentDirs()

        File(file.absPath + '').delete()
        f = open(file.absPath + '', 'xb+')

        try:

            for chunk in r.iter_content(chunk_size=chunkSize):
                f.write(chunk)
                received += len(chunk)
                al.getItem(p)[1] = format(received / totalSize * 100, '.2f') + '% ' + p
                al.getItem(p)[2] = received / totalSize

                if al.viewFollow:
                    al.lookAtItem(p)
                else:
                    al.drawAFrame()

        except BaseException as e:
            text3 = '与服务器的连接意外中断:\n'
            text3 += str(e.__repr__())+'\n'
            ts.addWindow(DialogWindow(text3, lambda: exit()))
            raise AssertionError

        if totalSize == 0:
            al.getItem(p)[2] = 1
            al.drawAFrame()

        f.close()
        al.getItem(p)[1] = '下载完成 ' + p

        if al.viewFollow:
            al.lookAtItem(p)
        else:
            al.drawAFrame()

    try:
        for p in hl.downloadList:
            file = td.append(p)
            downloadFile2(settings['url'] + 'resources/' + p, file, p)
    except AssertionError as e:
        return

    ts.addWindow(DialogWindow('没有需要更新的文件', lambda: exit()))

    if getattr(sys, 'frozen', False):  # 被打包以后
        command = infojson['RunWhenExit']

        if command != "":
            try:
                subprocess.call(command, shell=True)
            except BaseException as e:
                text = '执行RunWhenExit时发生了错误:\n'
                text += '要执行的命令: '+command+'\n'
                text += str(e.__repr__())+'\n'
                ts.addWindow(DialogWindow(text, lambda: exit()))
                return

    time.sleep(1.5)
    ts.quit()


if __name__ == "__main__":

    if sys.prefix == sys.base_prefix:  # 不在虚拟环境中
        setFont()
        setBuffer()

    ts = Terminal()
    al = AList()
    al.getComponent('title').title = smartStretch('正在连接到服务器')

    ts.addWindow(al)

    threading.Thread(target=work2, daemon=True).start()

    ts.mainLoop()
