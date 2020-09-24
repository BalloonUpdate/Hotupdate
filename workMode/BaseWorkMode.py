import re
import sys
from abc import ABC, abstractmethod

from utils.File import File


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

        if len(self.regexes) == 0:
            return False

        if path == self.getSelf():
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

    def getSelf(self):
        return File(sys.executable).relPath(self.basePath)

    def getSelfParent(self):
        return File(sys.executable).parent.relPath(self.basePath)

    def excludeSelf(self):
        if self.getSelf() in self.downloadList:
            self.downloadList.remove(self.getSelf())

        if self.getSelf() in self.deleteList:
            self.deleteList.remove(self.getSelf())

        if self.getSelfParent() in self.deleteList:
            self.deleteList.remove(self.getSelfParent())

    @abstractmethod
    def scan(self, dir: File, tree: list):
        pass

