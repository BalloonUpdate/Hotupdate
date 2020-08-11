from Terminal import Terminal
from window.BigButtonMenu import BigButtonMenu
from window.ListWindow import ListWindow
from window.component.CloseButton import CloseButton
from window.component.WindowTitle import WindowTitle


class AList(ListWindow):
    def __init__(self):
        super().__init__()

        self.addComponent("title", WindowTitle("A New Menu"))
        self.addComponent("close", CloseButton())

        for i in range(0, 50):
            self.add("text" + str(i), None)


class MainMenu(BigButtonMenu):
    def __init__(self, monopolyMode, maskMode):
        super().__init__(monopolyMode, maskMode)

        self.elapsedTime = 0

        self.addComponent("title", WindowTitle("Main Test Menu"))
        self.addComponent("close", CloseButton())

        self.add("Open New One", lambda win, item: win.addWindow(
            AList()
        ))

        self.add("Run Test", lambda win, item: win.execute(
            lambda: print("Hello World"), 3000
        ))

        self.add("Quit Test", lambda win, item: win.release())

    def onUpdate(self, deltaTime):
        self.elapsedTime += deltaTime

        if self.elapsedTime > 1000:
            self.elapsedTime = 0
            # print("aaaaa")


if __name__ == "__main__":
    ts = Terminal()

    ts.addWindow(MainMenu(monopolyMode=True, maskMode=True))

    ts.mainLoop()
