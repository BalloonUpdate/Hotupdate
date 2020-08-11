import curses
import logging
import random
from abc import abstractmethod, ABC

from window.component.ComponentContainer import ComponentContainer

logging.basicConfig(filename='logs.txt', level=logging.INFO)


def log2(text):
    logging.info("   " + text)


class AbstractWindow(ComponentContainer, ABC):
    """一个基本的窗口(抽象类),提供子窗口处理逻辑,鼠标事件处理逻辑,以及临时释放处理逻辑"""

    def __init__(self, monopolyMode, maskMode):
        super().__init__()

        self.screen = None
        self.parent = None
        self.subWindows = []  # 所有的子窗口

        self.monopolyMode = monopolyMode  # 独占模式,如果为True则不能点击本窗口外的其它区域,鼠标事件也会优先触发到本窗口
        self.maskMode = maskMode  # 独占模式为True时有效,如果是True则点击本窗口外的其它区域完全无效,否则会关闭掉本窗口

        self.hasDestroyedFlag = False  # 是否曾被销毁过
        self.refreshFlag = False  # 刷新标志,设为True表示需要进行一次刷新
        self.releaseFlag = False  # 释放标志(注意不是Destroy),设为True会释放这个窗口
        self.lastMousePosition = None  # (x, y)  # 上一次鼠标(点击/拖动/滚轮)事件的位置

    def debug(self, text):
        log2(str(self) + ": " + text)

    def execute(self, fun, delay=0):
        """在curses之外执行函数,因为是有命令回显的,执行完后会延迟delay毫秒然后再切回curses

        :param fun: 在curses之外执行函数
        :param delay: 执行完后的额外延迟
        """

        self.parent.execute(fun, delay)

    def addWindow(self, win, initialize=True):
        """创建一个子窗口

        :param win: 子窗口实例
        :param initialize: 立即进行初始化并绘制内容
        """

        if not isinstance(win, AbstractWindow):
            raise TypeError(f"The window must be a Window's instance, instead of {type(win)}")

        # 注册这个子窗口
        self.subWindows.append(win)

        if initialize:
            self.initializeSubWins()

    def noticeReleaseSubWindows(self):
        """当有子窗口设置release=True后需要手动调一下本方法来将那个子窗口彻底释放掉"""

        dl = []  # 避免边读边写

        # 寻找需要释放的子窗口
        for win in self.subWindows:
            if win.releaseFlag:
                dl.append(win)

        for d in dl:
            self.subWindows.remove(d)

        # 绘制一帧以填补子窗口释放之后的空白区域
        self.drawAFrame()

    def release(self):
        """释放本窗口"""

        self.releaseFlag = True  # 先设置释放标志位
        self.parent.noticeReleaseSubWindows()  # 然后通知父窗口来释放本窗口

    def drawAFrame(self):
        """绘制一帧"""

        self.refreshFlag = True

    def destroy(self):
        """临时性销毁本窗口,释放使用release()"""

        self.screen = None
        self.hasDestroyedFlag = True

        # 销毁所有子窗口
        for win in self.subWindows:
            win.destroy()

        self.onDestroy()  # 调用具体实现的函数
        self.distributeOnDestroy()  # 也把这个事件传递给组件们

    def trblToXywh(self, top, right, bottom, left):
        """将相对于个边的向内偏移量转换成坐标和长宽,(0,0,0,0)就是铺满父窗口
        通常用在onResize()里面，用于快速计算需要返回的值

        :returns: 计算好的坐标和长宽(x, y, w, h)
        :param top: 从顶部向内的偏移量,只能为正数
        :param right: 从右边向内的偏移量,只能为正数
        :param bottom: 从底部向内的偏移量,只能为正数
        :param left: 从坐标向内的偏移量,只能为正数
        """

        assert top >= 0 and right >= 0 and bottom >= 0 and left >= 0

        x = self.parent.x + left
        y = self.parent.y + top
        w = self.parent.width - right - left
        h = self.parent.height - bottom - top

        return x, y, w, h

    @property
    def isDestroyed(self):
        """是否处于销毁状态"""

        return self.screen is None

    def initialize(self, newScreen):
        """(重新)初始化本窗口

        :param newScreen: curses的screen对象
        """

        if not self.isDestroyed:
            raise self.NotDestroyedException("can't initialize")

        self.screen = newScreen

        if self.hasDestroyedFlag:
            self.onReinitialize()  # 调用具体实现的函数
            self.distributeOnReinitialize()  # 也把这个事件传递给组件们
        else:
            self.onInitialize()  # 调用具体实现的函数
            self.distributeOnInitialize()  # 也把这个事件传递给组件们

        # 也要初始化所有子窗口
        self.initializeSubWins()

        # 绘制一帧不然画面还是空白的
        self.drawAFrame()

    def initializeSubWins(self):
        """初始花所有子窗口"""

        for win in self.subWindows:
            if win.isDestroyed:
                win.parent = self

                x, y, w, h = win.onResize(self.width, self.height)

                assert 0 <= x < self.width, f"x: {x}"
                assert 0 <= y < self.height, f"y: {y}"
                assert 0 < w <= self.width + x, f"w: {w}, max: {self.width + x}"
                assert 0 < h <= self.height + y, f"h: {h}, max: {self.height + y}"

                win.initialize(self.screen.subwin(h, w, y, x))

    @property
    def absX(self):
        """窗口的绝对X轴坐标(相对于Terminal窗口)"""

        return self.parent.absX + self.x

    @property
    def absY(self):
        """窗口的绝对Y轴坐标(相对于Terminal窗口)"""

        return self.parent.absY + self.y

    @property
    def x(self):
        """窗口相对于父窗口的X轴坐标"""

        return self.screen.getparyx()[1]

    @property
    def y(self):
        """窗口相对于父窗口的Y轴坐标"""

        return self.screen.getparyx()[0]

    @property
    def width(self):
        """窗口宽度"""

        return self.screen.getmaxyx()[1]

    @property
    def height(self):
        """窗口高度"""

        return self.screen.getmaxyx()[0]

    def randomColor(self):
        """随机更换的一个笔刷颜色"""

        self.screen.attrset(curses.color_pair(random.randrange(1, 7)))

    def resetColor(self):
        """重置笔刷颜色"""

        self.screen.attrset(0)

    def hasMonopolist(self):
        """是否有独占的窗口"""

        return self.monopolist is not None

    @property
    def monopolist(self):
        """获取独占的那个窗口"""

        for win in self.subWindows:
            if win.monopolyMode:
                return win
        return None

    def belongsToWindow(self, x, y):
        """测试x,y是否在win内部, 参数x,y是父窗口范围内的坐标"""

        y1, x1 = self.screen.getparyx()
        y2, x2 = self.screen.getmaxyx()
        x2 += x1
        y2 += y1

        return x2 > x >= x1 and y2 > y >= y1

    def getSubWindowByXY(self, x, y):
        """获取指定位置的子窗口, 参数x,y是父窗口范围内的坐标"""

        for win in self.subWindows:
            if win.belongsToWindow(x, y):
                return win

        return None

    def passEvent(self, x, y, onXxx, *args):  # x,y是本窗口坐标
        """
        把事件传递给具体实现的对象

        :return: 是否是本窗口的事件
        :param x: 本窗口范围内的坐标
        :param y: 本窗口范围内的坐标
        :param onXxx: 具体的事件回调函数
        :param args: 事件回调的参数
        """

        self.lastMousePosition = (x, y)  # 记录一下点击位置

        win = self.getSubWindowByXY(x, y)

        if win is not None:  # 子窗口事件
            fn = onXxx.__name__.replace('on', '')  # 这里如果不遵守命名规范是会报错的
            first = fn[0].lower()
            fn = first + fn[1:]

            getattr(win, fn)(x - win.x, y - win.y, *args)  # 传递到子窗口

            return False
        else:  # 本窗口事件
            if self.hasMonopolist():
                if self.monopolist.maskMode:
                    curses.flash()  # 表示独占者禁止其它操作
                else:
                    self.monopolist.release()

                return False
            else:
                onXxx(x, y, *args)

                return True

    def update(self, deltaTime):
        """传递事件"""

        self.checkDestroyState("can't pass the update event")

        # 传递给所有子窗口
        for win in self.subWindows:
            win.update(deltaTime)

        self.onUpdate(deltaTime)

        self.distributeOnUpdate(deltaTime)  # 将这个事件传递给组件们

    def click(self, x, y):
        """传递事件"""

        self.checkDestroyState("can't pass the click event")

        if self.passEvent(x, y, self.onClick):
            self.distributeOnClick(x, y)  # 不是子窗口事件时才将这个事件传递给组件们

    def mouseWheel(self, x, y, directionUp):  # x,y均为0,没法使用,只能依靠self.lastClick
        """传递事件"""

        self.checkDestroyState("can't pass the mouse wheel event")

        x, y = self.lastMousePosition if self.lastMousePosition is not None else (0, 0)

        if self.passEvent(x, y, self.onMouseWheel, directionUp):
            self.distributeOnMouseWheel(x, y, directionUp)  # 不是子窗口事件时才将这个事件传递给组件们

    def draw(self, forceRefresh=False):

        if forceRefresh or self.refreshFlag:

            self.checkDestroyState("can't draw a frame")

            self.screen.erase()

            fullScreen = False

            for win in self.subWindows:
                if win.x == 0 and win.y == 0 \
                        and win.width == self.width \
                        and win.height == self.height:
                    fullScreen = True

            if not fullScreen:
                self.onDraw()  # 绘制本窗口

            self.distributeOnDraw()  # 也把这个事件传递给组件们

            self.screen.refresh()

            self.refreshFlag = False

        # 绘制子所有窗口,子窗口的绘制和本窗口是相互独立不影响的
        self.drawSubWins()

    def drawSubWins(self):
        """绘制所有的子窗口"""

        self.checkDestroyState("can't draw a frame")

        for win in self.subWindows:
            win.draw()

    def checkDestroyState(self, message):
        if self.isDestroyed:
            raise self.DestroyedException(message)

    def onInitialize(self):
        pass

    def onReinitialize(self):
        pass

    def onDestroy(self):
        pass

    @abstractmethod
    def onResize(self, width, height):
        pass

    @abstractmethod
    def onDraw(self):
        pass

    def onUpdate(self, deltaTime):
        pass

    def onClick(self, x, y):
        pass

    def onMouseWheel(self, x, y, directionUp):
        pass

    class DestroyedException(Exception):
        def __init__(self, more):
            super().__init__()
            self.message = more

        def __str__(self):
            attach = " and " + self.message
            return "The Window has been destroyed" + attach if self.message != "" else ""

    class NotDestroyedException(Exception):
        def __init__(self, more):
            super().__init__()
            self.message = more

        def __str__(self):
            attach = " and " + self.message
            return "The Window has not been destroyed yet" + attach if self.message != "" else ""
