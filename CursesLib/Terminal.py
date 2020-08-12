import curses
import os
import time
import platform

from .window.AbstractWindow import AbstractWindow

# 鼠标事件的对应代码(掩码)
KB = {
    "left":   {"release": 1 << 0,  "press": 1 << 1,  "click": 1 << 2,  "double": 1 << 3,  "triple": 1 << 4},
    "center": {"release": 1 << 5,  "press": 1 << 6,  "click": 1 << 7,  "double": 1 << 8,  "triple": 1 << 9},
    "right":  {"release": 1 << 10, "press": 1 << 11, "click": 1 << 12, "double": 1 << 13, "triple": 1 << 14},
    "wheel":  {"up": 1 << 16, "down": 1 << 21},
    "withCTRL": 1 << 27,
    "drag": 0 << 0
}


class Terminal(AbstractWindow):
    def __init__(self):
        super().__init__(False, False)
        self.exitFlag = False  # 退出标志,为True会退出Terminal.mainLoop的循环(退出程序)
        self.interruptFlag = False  # 打断标志,如果为True说明有函数需要在curses之外执行
        self.activeResize = platform.system() != 'Linux'  # 是否主动重新构建窗口(因为在Windows下有一些问题，但Linux没有)
        self.enableOnUpdate = True  # 是否启用onUpdate()事件

        # func: 需要在curses之外执行的那个函数
        # delay: 执行完上面那个函数之后等待的时间(好给用户多看几眼的机会,不至于一闪而过)
        self.functions = []  # (func, delay)

        self.lastUpdate = int(time.time() * 1000)  # 上次调用update的时间戳

    def execute(self, fun, delay=0):
        """在curses界面之外执行函数"""

        assert fun is not None, "The function is None"
        assert delay >= 0, "The delay can not be a negative: " + str(delay)

        self.functions.append((fun, delay))
        self.interruptFlag = True

    def addWindow(self, win):
        """添加一个子窗口"""
        super().addWindow(win, initialize=self.screen is not None)

    @staticmethod
    def initializeCurses(screen, getchTimeout):
        screen.clear()  # 清屏
        screen.timeout(getchTimeout)  # 设置getch()超时
        curses.mousemask(curses.ALL_MOUSE_EVENTS)  # 监听所有鼠标事件

        # 加入几个预设颜色
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_BLUE, 0)
            curses.init_pair(2, curses.COLOR_CYAN, 0)
            curses.init_pair(3, curses.COLOR_GREEN, 0)
            curses.init_pair(4, curses.COLOR_MAGENTA, 0)
            curses.init_pair(5, curses.COLOR_RED, 0)
            curses.init_pair(6, curses.COLOR_YELLOW, 0)
            curses.init_pair(7, curses.COLOR_WHITE, 0)

            curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(12, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def cursesLoop(self, screen):
        self.initializeCurses(screen, getchTimeout=20)

        # 关闭光标可见
        curses.curs_set(0)

        # 初始化自己以及所有子窗口
        self.initialize(screen)

        while not self.interruptFlag:

            if not self.getInput(screen):
                break

            # 没有子窗口时也需要终止执行
            if len(self.subWindows) == 0:
                self.exitFlag = True  # 彻底退出
                break

            if self.enableOnUpdate:
                self.callOnUpdate()

            # 绘制子窗口
            self.drawSubWins()

        # 销毁自己以及所有子窗口
        self.destroy()

        # 重新开启光标可见
        curses.curs_set(1)

    def callOnUpdate(self):
        now = int(time.time() * 1000)
        deltaTime = now - self.lastUpdate
        self.lastUpdate = now
        for w in self.subWindows:
            w.update(deltaTime)

    def getInput(self, screen):
        c = screen.getch()
        if c != -1:
            if 0 < c < 256:
                if chr(c) in 'qQ':
                    self.exitFlag = True
                    return False
            elif c == curses.KEY_RESIZE:
                if self.activeResize:
                    return False
            elif c == curses.KEY_MOUSE:
                mouseId, mouseX, mouseY, mouseZ, bState = curses.getmouse()

                if bState & KB["left"]['click']:
                    for w in self.subWindows:
                        if w.belongsToWindow(mouseX, mouseY):
                            w.click(mouseX - w.x, mouseY - w.y)

                elif bState & KB["wheel"]["up"]:
                    for w in self.subWindows:
                        w.mouseWheel(mouseX, mouseY, directionUp=True)  # x,y均为0,没法使用,但又非传递不可

                elif bState & KB["wheel"]["down"]:
                    for w in self.subWindows:
                        w.mouseWheel(mouseX, mouseY, directionUp=False)  # x,y均为0,没法使用,但又非传递不可

                elif bState & KB["drag"] == 0:
                    # self.debug('safsafsf: '+str(bState))
                    # self.debug('drag: ' + str(mouseX) + ', ' + str(mouseY) + '|' + bState)
                    for w in self.subWindows:
                        w.drag(mouseX, mouseY)

        return True

    def mainLoop(self):
        while not self.exitFlag:
            while len(self.functions) > 0:
                self.clearBuffer()
                self.functions[0][0]()
                time.sleep(self.functions[0][1] / 1000)
                self.functions = self.functions[1:]

            curses.wrapper(self.cursesLoop)

            self.interruptFlag = False

    def quit(self):
        self.exitFlag = True
        self.interruptFlag = True

    @staticmethod
    def clearBuffer():
        for i in range(0, os.get_terminal_size()[1]):
            print("")

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def absX(self):
        return 0

    @property
    def absY(self):
        return 0

    def onDraw(self):
        pass

    def onResize(self, width, height):
        return self.trblToXywh(0, 0, 0, 0)

    def __repr__(self):
        return 'Ternimal'
