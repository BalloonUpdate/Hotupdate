import re
import sys
from abc import ABC, abstractmethod

from src.newupdater.utils.file import File


class BaseWorkMode(ABC):
    def __init__(self, basePath, regexes, regexesMode):
        super().__init__()
        self.basePath: File = basePath
        self.deleteList: list = []
        self.downloadList: list = []
        self.downloadMap: dict = {}
        self.regexes: list = regexes
        self.regexesMode: bool = regexesMode  # True: AND mode, False: Or mode

    def delete(self, file: File):
        if file.isDirectory:
            for f in file:
                if 'tree' in f:
                    self.delete(f)
                else:
                    self.deleteList.append(f.relPath(self.basePath))
        self.deleteList.append(file.relPath(self.basePath))

    def download(self, node: dict, dir: File):
        if 'tree' in node:
            # 提前创建文件夹（即使是空文件夹）
            dir.append(node['name']).makeParentDirs()

            for n in node['tree']:
                dd = dir.append(n['name'])

                if 'tree' in n:
                    self.download(n, dd)
                else:
                    relPath = dd.relPath(self.basePath)
                    self.downloadList.append(relPath)
                    self.downloadMap[relPath] = n['length']
        else:
            relPath = dir.relPath(self.basePath)
            self.downloadList.append(relPath)
            self.downloadMap[relPath] = node['length']

    def test(self, path: str) -> bool:
        """测试指定的目录是否能通过正则表达式的匹配
        :param path: 需要测试的相对路径字符串
        :return: 是否通过了匹配
        """

        if len(self.regexes) == 0:
            return False

        results = [
            re.match(reg, path) is not None
            for reg in self.regexes
        ]

        result = self.regexesMode

        for r in results:
            if self.regexesMode:  # AND mode
                result &= r
            else:  # OR mode
                result |= r

        return result

    def excludeSelf(self):
        """将可执行文件本身给排除掉，主要用于打包以后的防误删机制"""
        selfExe = File(sys.executable).relPath(self.basePath)
        selfExeParent = File(sys.executable).parent.relPath(self.basePath)

        if selfExe in self.downloadList:
            self.downloadList.remove(selfExe)

        if selfExe in self.deleteList:
            self.deleteList.remove(selfExe)

        if selfExeParent in self.deleteList:
            self.deleteList.remove(selfExeParent)

    @abstractmethod
    def scan(self, dir: File, tree: list):
        pass
