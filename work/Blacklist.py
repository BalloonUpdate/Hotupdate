from File import File
from work.B import B


class Blacklist(B):

    def walk(self, dir: File, tree: list):
        for t in tree:
            d = dir.child(t['name'])

            if d.exists:
                if 'tree' not in t:  # 是文件
                    # if t['length'] == -1:  # 需要删除
                    #     self.delete(d)
                    # else:
                    if d.sha1 != t['hash']:
                        self.delete(d)
                        self.download(t, d)
                else:  # 是文件夹
                    # if 'length' in t:  # 需要删除整个文件夹
                    #     self.delete(d)
                    # else:
                    self.walk(d, t['tree'])
            else:
                self.download(t, d)

    def scan(self, dir: File, tree: list):
        self.walk(dir, tree)
