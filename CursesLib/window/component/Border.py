import curses

from .BaseComponent import BaseComponent


class Border(BaseComponent):
    """窗口边框"""

    def onWindowDraw(self):
        self.window.screen.box(curses.ACS_VLINE, curses.ACS_HLINE)
