import wx


class MainWindow(wx.Frame):
    def __init__(self, parent=None, title="MainWindow"):
        super().__init__(parent=parent, title=title)
        self.Center()

        a1 = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        a2 = wx.StaticText(self, label="Title")

        self.gSizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        self.gSizer.AddGrowableRow(0)

        self.gSizer.Add(a1, 1, wx.EXPAND)
        self.gSizer.SetCols(1)
        self.gSizer.Add(a2)

        # self.SetAutoLayout(True)
        # self.gSizer.Fit(self)
        self.SetSizer(self.gSizer)


app = wx.App(False)
win = MainWindow(title='窗口')

win.Show()

app.MainLoop()
