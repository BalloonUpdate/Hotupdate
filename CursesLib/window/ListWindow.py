import sys
from abc import ABC

from .AbstractWindow import AbstractWindow
from .component.Border import Border
from .component.ScrollBar import ScrollBar
from ..utils.ChineseSpace import insertSpaceBehindChinese


class ListWindow(AbstractWindow, ABC):
    def __init__(self, monopolyMode=False, maskMode=False):
        super().__init__(monopolyMode, maskMode)

        self.items = []  # (name, text, clickCb)
        self.scrollOffset = 0  # 控制列表滚动的偏移量

        self.addComponent("sb", ScrollBar())
        self.addComponent("border", Border())

    def onDraw(self):
        # 数据检查
        self.scrollOffset = min(self.scrollOffset, self.hiddenLines)
        self.scrollOffset = max(self.scrollOffset, 0)

        self.drawScrollBar()
        self.drawContents()

    def onResize(self, width, height):
        return self.trblToXywh(0, 0, 0, 0)

    @property
    def lines(self):
        """理论上可显示的最大行数(窗口高度)"""

        return self.height - 2

    @property
    def scrollPosition(self):
        """滚动栏进度(百分比)"""

        if self.hiddenLines == 0:
            return 0

        return self.scrollOffset / self.hiddenLines

    @property
    def displayLines(self):
        """实际最大显示行数"""

        return min(len(self.items), self.lines)

    @property
    def hiddenLines(self):
        """被隐藏的行数"""

        return len(self.items) - self.displayLines

    def drawScrollBar(self):
        """绘制滚动栏"""

        if self.hiddenLines == 0:
            self.getComponent("sb").viewProportion = 0
            return

        self.getComponent("sb").viewProportion = self.displayLines / len(self.items)
        self.getComponent("sb").progress = self.scrollPosition

    def drawContents(self):
        """绘制所有内容"""

        for i in range(0, self.displayLines):
            item = self.items[i + self.scrollOffset]
            text = item[1]
            text = text[:self.width - 5]

            if sys.prefix == sys.base_prefix:
                text = insertSpaceBehindChinese(text)

            self.screen.addstr(i + 1, 2, text)

    def addItem(self, name, text=None, onClick=None, *args):
        """添加一个项目"""

        if text==None:
            text = name

        self.items.append([name, text, onClick, *args])

        self.drawAFrame()

    def clearItems(self):
        """干掉所有项目"""

        self.items.clear()

    def removeItem(self, name):
        di = []
        index = 0

        for i in self.items:
            if i[0] == name:
                di.append(index)
                index += 1

        for d in di:
            del self.items[d]

    def getItem(self, name):
        for i in self.items:
            if i[0] == name:
                return i

    def onClick(self, x, y):
        if self.width - 2 > x > 0 and self.height - 1 > y > 0:
            i = y - 1
            if i < self.displayLines:
                item = self.items[i + self.scrollOffset]
                if item[2] is not None:
                    item[2](self, item, x, y)
                self.drawAFrame()

    def onMouseWheel(self, x, y, directionUp):

        if directionUp:
            self.scrollOffset -= 1
        else:
            self.scrollOffset += 1

        self.drawAFrame()

    def __repr__(self):
        return 'ListWindow'
