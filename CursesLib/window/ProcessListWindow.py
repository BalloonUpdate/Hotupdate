import curses
from abc import ABC

from .AbstractWindow import AbstractWindow
from .component.Border import Border
from .component.ScrollBar import ScrollBar
from ..utils.ChineseSpace import smartStretch


class ProcessListWindow(AbstractWindow, ABC):
    def __init__(self, monopolyMode=False, maskMode=False):
        super().__init__(monopolyMode, maskMode)

        self.items = []  # (name, text, process, clickCb)
        self.scrollOffset = 0  # 控制列表滚动的偏移量
        self.viewFollow = True  # 视野跟随，如果关闭的话LookAtItem将不再强制滚屏

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
            text = smartStretch(text)

            rowWidth = self.width - 2
            process = item[2]
            sp = (rowWidth - 2) * process
            for p in range(0, rowWidth - 2):
                ch = text[p] if p < len(text) else ' '

                if process == -1:
                    cp = 12
                else:
                    if process >= 1:
                        cp = 3  # green over black
                    else:
                        if p >= sp or process >= 1:
                            cp = 10
                        else:
                            cp = 11

                self.screen.attrset(curses.color_pair(cp))

                self.screen.addstr(i + 1, 2 + p, ch)
            self.resetColor()

            # self.screen.addstr(i + 1, 2, text)

    def addItem(self, name, text, process=0, onClick=None):
        """添加一个项目"""

        self.items.append([name, text, process, onClick])

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

    def getItemIndex(self, name):
        index = 0
        for i in self.items:
            if i[0] == name:
                return index
            index += 1
        return index

    def lookAtItem(self, name):
        idx = self.getItemIndex(name)
        rPoint = 0.6 * self.lines
        if len(self.items) > self.lines:
            idxInScreen = idx - self.scrollOffset
            if idxInScreen >= rPoint:
                self.scrollOffset += int(idxInScreen - rPoint)

        self.drawAFrame()

    def onClick(self, x, y):
        if self.width - 2 > x > 0 and self.height - 1 > y > 0:
            i = y - 1
            if i < self.displayLines:
                item = self.items[i + self.scrollOffset]
                if item[3] is not None:
                    item[3](self, item, x, y)
                self.drawAFrame()

    def onMouseWheel(self, x, y, directionUp):

        self.viewFollow = False  # 动过滚轮之后就不再锁定屏幕了

        if directionUp:
            self.scrollOffset -= 1
        else:
            self.scrollOffset += 1

        self.drawAFrame()

    def __repr__(self):
        return 'ListWindow'
