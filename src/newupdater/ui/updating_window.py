import sys
import typing

from PyQt5 import QtGui
from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont, QShowEvent, QIcon
from PyQt5.QtWidgets import QVBoxLayout, QListView, QMessageBox, QApplication, QMainWindow, QWidget
from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress

from src.newupdater.utils.file import File
from src.newupdater.utils.logger import info


class UpdatingWindowDataSource(QAbstractListModel):
    def __init__(self, *args1, **args2):
        super().__init__(*args1, **args2)

        self.dataSet = []  # [path, display, isBold]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.dataSet)

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:

        if role == Qt.DisplayRole:
            item = self.dataSet[index.row()]
            return item[1]

        if role == Qt.FontRole:
            item = self.dataSet[index.row()]
            if item[2]:
                font = QFont()
                font.setBold(True)
                return font

    def appendFile(self, filePath: str, display: str):
        self.dataSet.append([filePath, display, False])
        self.notifyDataChanged()
        return self.rowCount() + 1

    def findFile(self, filePath: str) -> int:
        index = 0
        for f in self.dataSet:
            if f[0] == filePath:
                return index
            index += 1
        return -1

    def setItemText(self, filePath: str, display: str):
        i = self.findFile(filePath)

        if i != -1:
            self.dataSet[i][1] = display
            self.notifyDataChanged()
        return i

    def notifyDataChanged(self):
        start = self.createIndex(0, 0)
        end = self.createIndex(self.rowCount() - 1, 0)
        self.dataChanged.emit(start, end)


class UpdatingWindow(QMainWindow):
    es_showMessageBox = pyqtSignal(str, str)
    es_setShow = pyqtSignal(bool)
    es_close = pyqtSignal()
    es_addItem = pyqtSignal(str, str)
    es_setItemText = pyqtSignal(str, str, bool)
    es_setItemBold = pyqtSignal(str, bool)
    es_setWindowTitle = pyqtSignal(str)
    es_setWindowWidth = pyqtSignal(int)
    es_setWindowHeight = pyqtSignal(int)
    es_setWindowCenter = pyqtSignal()
    es_setProgressStatus = pyqtSignal(int)
    es_setProgressRange = pyqtSignal(int, int)
    es_setProgressValue = pyqtSignal(int)
    es_setProgressVisible = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.taskbarButton: QWinTaskbarButton = None
        self.taskbarProgress: QWinTaskbarProgress = None
        self.showTaskbarProgress = False
        self.lastTaskbarProgressRange = [0, 0]

        self.resize(480, 350)
        self.setWindowTitle('UpdatingWindow')

        self.tasks = []

        view = QListView()
        model = UpdatingWindowDataSource()

        view.setModel(model)

        self.setCentralWidget(view)

        dir = File(getattr(sys, '_MEIPASS', ''))
        self.setWindowIcon(QIcon(dir('icon.ico').path))

        self.model = model
        self.view = view

        self.es_showMessageBox.connect(self._showMessageBox)
        self.es_setShow.connect(self._setShow)
        self.es_addItem.connect(self._addItem)
        self.es_setItemText.connect(self._setItemText)
        self.es_setWindowTitle.connect(self._setWindowTitle)
        self.es_setWindowWidth.connect(self._setWindowWidth)
        self.es_setWindowHeight.connect(self._setWindowHeight)
        self.es_setWindowCenter.connect(self._setWindowCenter)
        self.es_setProgressStatus.connect(self._setProgressStatus)
        self.es_setProgressRange.connect(self._setProgressRange)
        self.es_setProgressValue.connect(self._setProgressValue)
        self.es_setProgressVisible.connect(self._setProgressVisible)
        self.es_setItemBold.connect(self._setItemBold)
        self.es_close.connect(self._close)

    def _showMessageBox(self, message, title):
        msgBox = QMessageBox()
        msgBox.setText(message)
        msgBox.setWindowTitle(title)
        msgBox.exec_()

    def _setShow(self, show: bool):
        self.setVisible(show)

    def _addItem(self, path: str, display: str):
        index = self.model.appendFile(path, display)
        self.view.scrollTo(self.model.createIndex(min(self.model.rowCount(), index+4), 0))

    def _setItemText(self, path: str, display: str, lookAt: bool):
        index = self.model.setItemText(path, display)
        if lookAt:
            self.view.scrollTo(self.model.createIndex(min(self.model.rowCount(), index+4), 0))

    def _setItemBold(self, path: str, isBold: bool):
        index = self.model.findFile(path)
        self.model.dataSet[index][2] = isBold

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

    def _setProgressStatus(self, status: int):
        def b():
            if status == 0:
                self.taskbarProgress.resume()
            if status == 1:
                self.taskbarProgress.pause()
            if status == 2:
                self.taskbarProgress.stop()

        if self.taskbarButton is not None and True:
            b()
        else:
            self.tasks.append(b)
            # self.delayExecuting(b, 5)

    def _setProgressRange(self, minimum, maximum):
        self.taskbarProgress.setRange(minimum, maximum)
        self.lastTaskbarProgressRange = [minimum, maximum]

    def _setProgressValue(self, value):
        self.taskbarProgress.setValue(value)

    def _setProgressVisible(self, visible):
        self.taskbarProgress.setVisible(visible)
        self.showTaskbarProgress = visible

    def _close(self):
        self.close()

    def showEvent(self, event: QShowEvent) -> None:

        def b():
            # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

            button = QWinTaskbarButton()
            button.setWindow(self.windowHandle())

            progress = button.progress()

            self.taskbarButton = button
            self.taskbarProgress = progress

            while len(self.tasks) > 0:
                info('执行队列')
                self.tasks.pop(0)()

        self.delayExecuting(func=b, delayInSec=5)

    def changeEvent(self, e: QEvent) -> None:
        if e.type() != QEvent.WindowStateChange:
            return

        if self.windowState() == Qt.WindowNoState:

            def b():
                self.taskbarProgress.setRange(*self.lastTaskbarProgressRange)
                self.taskbarProgress.setVisible(True)

            timer = QTimer(self)
            timer.setInterval(50)
            timer.setSingleShot(True)
            timer.timeout.connect(b)
            timer.start()

    def delayExecuting(self, func, delayInSec):
        timer = QTimer(self)
        timer.setInterval(delayInSec)
        timer.setSingleShot(True)
        timer.timeout.connect(func)
        timer.start()
