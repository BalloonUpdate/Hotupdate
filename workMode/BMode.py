from utils.File import File
from workMode.BaseWorkMode import BaseWorkMode


class BMode(BaseWorkMode):
    """
    默认只同步存在于服务器的上的文件，服务器没有的文件不做任何变动
    如果指定了正则表达式，则会使用正则表达式进行删除
    匹配的文件会直接被删除，即使是存在于服务器的上的文件也是如此(高优先级)
    不匹配的文件会被忽略掉，并按第一行的规则进行处理
    """

    def walk(self, dir: File, tree: list, base: File):

        for d in dir:
            self.debug(str(self.test(d.relPath(base))) + ': ' + d.relPath(base))

            if self.test(d.relPath(base)) and len(self.regexes) != 0:
                self.delete(d)
                continue

        for t in tree:
            d = dir.append(t['name'])

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
                    self.walk(d, t['tree'], base)
            else:
                self.download(t, d)

    def scan(self, dir: File, tree: list):
        self.walk(dir, tree, dir)
