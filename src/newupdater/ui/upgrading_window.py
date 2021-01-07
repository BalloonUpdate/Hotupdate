import subprocess
import sys
import time

from PyQt5.QtCore import QAbstractListModel, pyqtSignal, QModelIndex, QTimer, QEvent, Qt
from PyQt5.QtGui import QFont, QShowEvent, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListView, QMessageBox, QMainWindow
from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress

from src.newupdater.utils.file import File
from src.newupdater.utils.logger import info


class UpgradingWindowDataSource(QAbstractListModel):
    def __init__(self, *args1, **args2):
        super().__init__(*args1, **args2)

        self.dataSet = []  # [[path, display, isBold]]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.dataSet)

    def data(self, index: QModelIndex, role: int = ...):
        if role == Qt.DisplayRole:
            return str(self.dataSet[index.row()][1])

        if role == Qt.FontRole:
            item = self.dataSet[index.row()]
            if item[2]:
                font = QFont()
                font.setBold(True)
                return font

    def appendFile(self, filePath: str, display: str):
        self.dataSet.append([filePath, display, False])
        self.notifyDataChanged()
        return self.rowCount()

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


class UpgradingWindow(QMainWindow):
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

        self.resize(420, 300)
        self.setWindowTitle('UpgradingWindow')

        self.tasksDependOnWindow = []  # [func]
        self.pendingTasks = []  # [[time, func]]

        view = QListView()
        model = UpgradingWindowDataSource()

        view.setModel(model)

        self.setCentralWidget(view)

        dir = File(getattr(sys, '_MEIPASS', ''))
        self.setWindowIcon(QIcon(dir('icon.ico').path))

        self.model = model
        self.view = view

        # Entry instance
        self.e = None

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

        self.initializeTimer()

    def _showMessageBox(self, message, title):
        jsondata = self.e.getSettingsJson()
        if 'error_message' in jsondata:
            message += '\n\n'+jsondata['error_message']

        msgBox = QMessageBox()
        if 'error_help' in jsondata:
            msgBox.addButton(QMessageBox.StandardButton.Open)
        msgBox.addButton(QMessageBox.StandardButton.Ok)
        msgBox.setText(message)
        msgBox.setWindowTitle(title)
        msgBox.exec_()

        if 'error_help' in jsondata:
            if msgBox.result() == QMessageBox.StandardButton.Open:
                cmd = jsondata['error_help']
                subprocess.call(f'cd /D "{self.e.exe.parent.parent.parent.windowsPath}" && {cmd}', shell=True)

    def _setShow(self, show: bool):
        self.setVisible(show)

    def _addItem(self, path: str, display: str):
        index = self.model.appendFile(path, display)
        self.view.scrollTo(self.model.createIndex(min(self.model.rowCount(), index + 4), 0))

    def _setItemText(self, path: str, display: str, lookAt: bool):
        index = self.model.setItemText(path, display)
        if lookAt:
            self.view.scrollTo(self.model.createIndex(min(self.model.rowCount(), index + 4), 0))

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
        self.move(int((desktop.width() - self.width()) / 2), int((desktop.height() - self.height()) / 2))

    def _setProgressStatus(self, status: int):
        if status == 0:
            self.taskbarProgress.resume()
        if status == 1:
            self.taskbarProgress.pause()
        if status == 2:
            self.taskbarProgress.stop()

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
            button = QWinTaskbarButton()
            button.setWindow(self.windowHandle())

            progress = button.progress()

            self.taskbarButton = button
            self.taskbarProgress = progress

            while len(self.tasksDependOnWindow) > 0:
                task = self.tasksDependOnWindow.pop(0)
                task()

        self.delayExecuting(func=b, delay=5)

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

    def initializeTimer(self):
        def ex():
            now = int(time.time() * 1000)

            expired = []
            for i in range(0, len(self.pendingTasks)):
                task = self.pendingTasks[i]
                if now - task[0] >= 0:
                    task[1]()
                    expired.append(i)
                    info('执行队列 ' + str(len(self.pendingTasks)))
            for e in expired:
                self.pendingTasks.pop(e)

        self.timer = QTimer(self)
        self.timer.setInterval(5)
        self.timer.timeout.connect(ex)
        self.timer.start()
        info('定时器已启动')

    def delayExecuting(self, func, delay=5):
        task = [int(time.time() * 1000) + delay, func]
        self.pendingTasks.append(task)
        info('添加任务')
