from abc import ABC, abstractmethod

from File import File


class B(ABC):
    def __init__(self, basePath):
        super().__init__()
        self.basePath: File = basePath
        self.deleteList: list = []
        self.downloadList: list = []

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
                dd = dir.child(n['name'])

                if 'tree' in n:
                    self.download(n, dd)
                else:
                    self.downloadList.append(dd.relPath(self.basePath))
        else:
            self.downloadList.append(dir.relPath(self.basePath))

    @abstractmethod
    def scan(self, dir: File, tree: list):
        pass

