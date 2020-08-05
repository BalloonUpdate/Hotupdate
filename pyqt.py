import sys

from PyQt5.QtWidgets import QApplication, QWidget

app = QApplication(sys.argv)


class EW(QWidget):
    def __init__(self):
        super().__init__()

        self.resize(300, 200)
        self.setWindowTitle('simple')


w = EW()
w.show()

sys.exit(app.exec_())
