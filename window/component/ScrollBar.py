import curses

from window.component.BaseComponent import BaseComponent


class ScrollBar(BaseComponent):
	"""滚动条组件"""

	def __init__(self):
		super().__init__()

		self.trbl = (2, 2, 2, -2)

		self.progress = 0  # 滚动条的滚动进度(0~1)
		self.viewProportion = 0  # 滚动条的可视比例(0~1)

	def onWindowDraw(self):
		progress = self.progress
		viewProportion = self.viewProportion

		if not (0 <= progress <= 1 and 0 < viewProportion <= 1):
			return
		# assert False, f"progress: {progress}, viewProportion: {viewProportion}"

		x1, y1, x2, y2, w, h = self.getXyxywh()

		# mark 滚动条实体 / background 滚动条背景
		bgLen = h
		markLen = int(bgLen * viewProportion)

		blankPer = 1 - viewProportion
		move = int((bgLen * blankPer) * progress)

		if progress == 1:
			move += bgLen - markLen - move

		if markLen > 0:
			assert 0 < bgLen + y1 <= self.window.height, f"bgLen: {bgLen}, y1: {y1}, both: {y1 + bgLen}, h: {h}, self: {str(self.window)}, p: {self.getXyxywh()}, {self.trbl}"
			self.window.screen.vline(y1, x1, curses.ACS_BOARD, bgLen)
			self.window.screen.vline(y1 + move, x1, curses.ACS_BLOCK, markLen)

	# 调试用的，应该由本组件所属的窗口自己去控制progress和viewProportion属性，而不是由本组件的事件函数去控制，故注释
	# def onWindowMouseWheel___________________(self, x, y, directionUp):
	#
	# 	if not directionUp:
	# 		self.progress += 0.1
	# 	else:
	# 		self.progress -= 0.1
	#
	# 	self.progress = self.clamp(0, 1, self.progress)
	#
	# 	self.window.drawAFrame()
