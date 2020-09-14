import curses
import platform

from .component.CloseButton import CloseButton
from ..utils.ChineseSpace import smartStretch, split
from .AbstractWindow import AbstractWindow
from .component.Border import Border
from .component.WindowTitle import WindowTitle


class DialogWindow(AbstractWindow):
    """窗口标题组件"""

    def __init__(self, message: str, callback, title=None):
        super().__init__(monopolyMode=True, maskMode=True)
        self.message = message
        self.callback = callback
        self.buttonWidth = 50
        self.buttonHeight = 4

        self.addComponent("border", Border())
        self.addComponent("title", WindowTitle(''))

        self.setTitle(title)

        if not platform.platform().startswith('Windows-10'):
            border = self.getComponent('border')
            border.enable = False

    def onDraw(self):
        yDelta = 0
        for line in split(smartStretch(self.message), self.width - 4):
            self.screen.addstr(1 + yDelta, 2, line)
            yDelta += 1

            if yDelta >= self.height - 10:
                self.screen.addstr(1 + yDelta, 2, 'and more ...')
                break

        t, r, b, l = self.getButtonRect()

        text = smartStretch('确定')
        strLen = len(text)
        self.screen.addstr(t + 2, max(1, int((l + r) / 2 - strLen / 2)), text)

        self.screen.addstr(self.height - 2, 2, smartStretch('Tips: 请使用鼠标点击操作,而不是键盘'))

        if platform.platform().startswith('Windows-10'):
            self.screen.hline(t, l, curses.ACS_HLINE, self.buttonWidth)
            self.screen.hline(b, l, curses.ACS_HLINE, self.buttonWidth)
            self.screen.vline(t, l, curses.ACS_VLINE, self.buttonHeight + 1)
            self.screen.vline(t, r, curses.ACS_VLINE, self.buttonHeight + 1)
            self.screen.addch(t, l, curses.ACS_ULCORNER)
            self.screen.addch(t, r, curses.ACS_URCORNER)
            self.screen.addch(b, l, curses.ACS_LLCORNER)
            self.screen.addch(b, r, curses.ACS_LRCORNER)
        else:
            self.screen.hline(t, l, '#', self.buttonWidth)
            self.screen.hline(b, l, '#', self.buttonWidth)
            self.screen.vline(t, l, '#', self.buttonHeight + 1)
            self.screen.vline(t, r, '#', self.buttonHeight + 1)
            self.screen.addch(t, l, '#')
            self.screen.addch(t, r, '#')
            self.screen.addch(b, l, '#')
            self.screen.addch(b, r, '#')

    def onResize(self, width, height):
        return self.trblToXywh(0, 0, 0, 0)

    def onClick(self, x, y):
        t, r, b, l = self.getButtonRect()

        if l <= x <= r and t <= y <= b:
            self.callback()
            self.release()

    def getButtonRect(self):
        l = self.width // 2 - self.buttonWidth // 2
        r = l + self.buttonWidth
        t = self.height - 3 - self.buttonHeight
        b = t + self.buttonHeight
        return t, r, b, l

    def setTitle(self, text: str):
        enable = text is not None and len(text) != 0
        self.getComponent('title').enable = enable
        self.getComponent('title').title = smartStretch(text) if enable else ''
