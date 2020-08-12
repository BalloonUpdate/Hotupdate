class BaseComponent:
	"""一个组件的基本类"""

	def __init__(self):
		self.window = None  # initialize by ComponentContainer
		self.trbl = (0, 0, 0, 0)  # 四边向中心进行定位(t,r,b,l),如果某个值为负数则从对面开始定位
		self.enable = True

	def getXyxywh(self):
		"""返回可直接用于curses绘制的相对坐标"""

		top = self.trbl[0]
		right = self.trbl[1]
		bottom = self.trbl[2]
		left = self.trbl[3]

		x1 = 0
		y1 = 0
		x2 = self.window.width + x1
		y2 = self.window.height + y1

		# 为负数时就从对面开始定位
		cpx1 = x1 + left if left >= 0 else x2 + left
		cpy1 = y1 + top if top >= 0 else y2 + top
		cpx2 = x2 - right if right >= 0 else x1 - right
		cpy2 = y2 - bottom if bottom >= 0 else y1 - bottom

		fx1 = min(cpx1, cpx2)
		fy1 = min(cpy1, cpy2)
		fx2 = max(cpx1, cpx2)
		fy2 = max(cpy1, cpy2)

		width = abs(cpx2 - cpx1)
		height = abs(cpy2 - cpy1)

		assert fx1 >= x1 and fy1 >= y1 and fx2 <= x2 and fy2 <= y2

		return fx1, fy1, fx2, fy2, width, height

	@staticmethod
	def clamp(minV, maxV, value):
		if minV > maxV:
			_temp = minV
			minV = maxV
			maxV = _temp
		return min(maxV, max(minV, value))

	def onWindowInitialize(self):
		pass

	def onWindowReinitialize(self):
		pass

	def onWindowDestroy(self):
		pass

	def onWindowDraw(self):
		pass

	def onWindowClick(self, x, y):
		pass

	def onWindowMouseWheel(self, x, y, directionUp):
		pass

	def onWindowDrag(self, x, y):
		pass

	def onWindowUpdate(self, deltaTime):
		pass
