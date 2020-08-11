from abc import ABC

from window.AbstractWindow import AbstractWindow
from window.component.Border import Border
from window.component.ScrollBar import ScrollBar


class ListWindow(AbstractWindow, ABC):
	def __init__(self, monopolyMode=False, maskMode=False):
		super().__init__(monopolyMode, maskMode)

		self.items = []  # (text, clickCb)
		self._scrollOffset = 0  # 控制列表滚动的偏移量

		self.addComponent("sb", ScrollBar())
		self.addComponent("border", Border())

	def onDraw(self):
		# 数据检查
		self._scrollOffset = min(self._scrollOffset, self.hiddenLines)
		self._scrollOffset = max(self._scrollOffset, 0)

		self.drawScrollBar()
		self.drawContents()

	def onResize(self, width, height):
		return self.trblToXywh(0, 0, 0, 0)

	@property
	def lines(self):
		"""可显示的行数"""

		return self.height - 2

	@property
	def scrollPosition(self):
		"""滚动栏进度(百分比)"""

		if self.hiddenLines == 0:
			return 0

		return self._scrollOffset / self.hiddenLines

	@property
	def displayLines(self):
		"""实际能显示的行数"""

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
			text = self.items[i + self._scrollOffset][0]
			self.screen.addstr(i + 1, 2, text[:self.width - 5])

	def add(self, text, onClick, *args):
		"""添加一个项目"""

		self.items.append((text, onClick, *args))
		self.drawAFrame()

	def clearItems(self):
		"""干掉所有项目"""

		self.items.clear()

	def onClick(self, x, y):
		if self.width - 2 > x > 0 and self.height - 1 > y > 0:
			i = y - 1
			if i < self.displayLines:
				item = self.items[i + self._scrollOffset]
				if item[1] is not None:
					item[1](self, item, x, y)
				self.drawAFrame()

	def onMouseWheel(self, x, y, directionUp):

		if directionUp:
			self._scrollOffset -= 1
		else:
			self._scrollOffset += 1

		self.drawAFrame()
