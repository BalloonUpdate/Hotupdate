import re
from abc import ABC, abstractmethod

from utils.File import File

# logging.basicConfig(filename='logs.txt', level=logging.INFO)
#
#
# def log2(text):
#     logging.info(" " + text)


class BaseWorkMode(ABC):
    def __init__(self, basePath, regexes, regexesMode):
        super().__init__()
        self.basePath: File = basePath
        self.deleteList: list = []
        self.downloadList: list = []
        self.downloadMap: dict = {}
        self.regexes: list = regexes
        self.regexesMode: bool = regexesMode  # True: AND mode, False: Or mode

    def delete(self, dir: File):

        if dir.isDirectory:
            for f in dir:
                if 'tree' in f:
                    self.delete(f)
                else:
                    self.deleteList.append(f.relPath(self.basePath))
        self.deleteList.append(dir.relPath(self.basePath))

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

    def test(self, path) -> bool:

        if len(self.regexes) == 0:
            return True

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

    @abstractmethod
    def scan(self, dir: File, tree: list):
        pass

    def debug(self, text):
        # log2(str(self.__class__) + ": " + text)
        pass
