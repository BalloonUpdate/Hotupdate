from window.component.BaseComponent import BaseComponent


class CloseButton(BaseComponent):
	"""关闭按钮"""

	def __init__(self):
		super().__init__()

		self.positionX = 4  # 相对于x2的坐标
		self.allowError = 1  # 点击判定范围

	def onWindowDraw(self):
		self.window.screen.addstr(0, self.window.width - self.positionX - 1, ' X ')

	def onWindowClick(self, x, y):
		errorX = abs(x - (self.window.width - self.positionX))

		if errorX <= self.allowError and y == 0:  # 点到了x
			self.window.release()
