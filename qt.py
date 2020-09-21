import typing

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QShowEvent, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QMessageBox
from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress


class DP(QAbstractListModel):
    def __init__(self, *args1, **args2):
        super().__init__(*args1, **args2)

        self.dataSet = []  # [path, display]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.dataSet)

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:

        if role == Qt.DisplayRole:
            item = self.dataSet[index.row()]
            return item[1]

        if role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

    def appendFile(self, filePath: str, display: str):
        self.dataSet.append([filePath, display])
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


class MyMainWindow(QWidget):

    es_showMessageBox = pyqtSignal(str, str)
    es_setShow = pyqtSignal(bool)
    es_addItem = pyqtSignal(str, str)
    es_setItemText = pyqtSignal(str, str, bool)
    es_setWindowTitle = pyqtSignal(str)
    es_setProgressStatus = pyqtSignal(int)
    es_setProgressRange = pyqtSignal(int, int)
    es_setProgressValue = pyqtSignal(int)
    es_setProgressVisible = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.taskbarButton: QWinTaskbarButton = None
        self.taskbarProgress: QWinTaskbarProgress = None

        self.resize(480, 350)
        self.setWindowTitle('simple')

        vbox = QVBoxLayout()

        view = QListView()
        model = DP()

        view.setModel(model)

        vbox.addWidget(view)

        self.setLayout(vbox)

        self.model = model
        self.view = view

        self.es_showMessageBox.connect(self._showMessageBox)
        self.es_setShow.connect(self._setShow)
        self.es_addItem.connect(self._addItem)
        self.es_setItemText.connect(self._setItemText)
        self.es_setWindowTitle.connect(self._setWindowTitle)
        self.es_setProgressStatus.connect(self._setProgressStatus)
        self.es_setProgressRange.connect(self._setProgressRange)
        self.es_setProgressValue.connect(self._setProgressValue)
        self.es_setProgressVisible.connect(self._setProgressVisible)

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

    def _setWindowTitle(self, text: str):
        self.setWindowTitle(text)

    def _setProgressStatus(self, status: int):
        if status == 0:
            self.taskbarProgress.resume()
        if status == 1:
            self.taskbarProgress.pause()
        if status == 2:
            self.taskbarProgress.stop()

    def _setProgressRange(self, minimum, maximum):
        self.taskbarProgress.setRange(minimum, maximum)

    def _setProgressValue(self, value):
        self.taskbarProgress.setValue(value)

    def _setProgressVisible(self, visible):
        self.taskbarProgress.setVisible(visible)

    def showEvent(self, event: QShowEvent) -> None:

        def b():
            button = QWinTaskbarButton()
            button.setWindow(self.windowHandle())

            progress = button.progress()

            self.taskbarButton = button
            self.taskbarProgress = progress

        timer = QTimer(self)
        timer.setInterval(5)
        timer.setSingleShot(True)
        timer.timeout.connect(b)
        timer.start()
