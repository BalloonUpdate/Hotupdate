import sys

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QHBoxLayout, QWidget

from src.utils.file import File


class SplashWindow(QMainWindow):
    es_setWindowTitle = pyqtSignal(str)
    es_setWindowWidth = pyqtSignal(int)
    es_setWindowHeight = pyqtSignal(int)
    es_setWindowCenter = pyqtSignal()
    es_setShow = pyqtSignal(bool)
    es_close = pyqtSignal()
    es_setText = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.resize(280, 180)
        self.setWindowTitle('SplashWindow')

        dir = File(getattr(sys, '_MEIPASS', ''))
        self.setWindowIcon(QIcon(dir('icon.ico').path))

        # 布局
        self.box = QHBoxLayout()

        self.label = QLabel('QLabel')
        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.box.addWidget(self.label, alignment=Qt.AlignCenter)

        temp = QWidget()
        temp.setLayout(self.box)
        self.setCentralWidget(temp)

        self.es_setWindowTitle.connect(self._setWindowTitle)
        self.es_setWindowWidth.connect(self._setWindowWidth)
        self.es_setWindowHeight.connect(self._setWindowHeight)
        self.es_setWindowCenter.connect(self._setWindowCenter)
        self.es_setText.connect(self._setText)
        self.es_setShow.connect(self._setShow)
        self.es_close.connect(self._close)

    def _setText(self, text: str):
        self.label.setText(text)

    def _setWindowTitle(self, text: str):
        self.setWindowTitle(text)

    def _setWindowWidth(self, width: int):
        size = self.size()
        size.setWidth(width)
        self.resize(size)

    def _setWindowHeight(self, height: int):
        size = self.size()
        size.setHeight(height)
        self.resize(size)

    def _setWindowCenter(self):
        desktop = QApplication.desktop()
        self.move((desktop.width() - self.width()) / 2, (desktop.height() - self.height()) / 2)

    def _setShow(self, show: bool):
        self.setVisible(show)

    def _close(self):
        self.close()


if __name__ == '__main__':
    qt = QApplication(sys.argv)

    win = SplashWindow()
    win.show()

    qt.exec_()
