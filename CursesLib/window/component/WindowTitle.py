import curses

from .BaseComponent import BaseComponent


class WindowTitle(BaseComponent):
    """窗口标题组件"""

    def __init__(self, title):
        super().__init__()
        self.title = title
        self.space = True  # 是否在标题文字两端留出空白

    def onWindowDraw(self):
        if not self.title.isspace():
            textLen = len(self.title) + (2 if self.space else 0)
            offsetX = int(self.window.width / 2 - textLen / 2)
            titleText = f" {self.title} " if self.space else self.title

            self.window.screen.addstr(0, offsetX, titleText)
