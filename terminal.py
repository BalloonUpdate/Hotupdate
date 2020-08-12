import platform
import time
from ctypes import *

LF_FACESIZE = 32
STD_OUTPUT_HANDLE = -11

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_CXMIN = 28
SM_CYMIN = 29


class COORD(Structure):
    _fields_ = [
        ("X", c_short),
        ("Y", c_short)
    ]


class CONSOLE_FONT_INFOEX(Structure):
    _fields_ = [
        ("cbSize", c_ulong),
        ("nFont", c_ulong),
        ("dwFontSize", COORD),
        ("FontFamily", c_uint),
        ("FontWeight", c_uint),
        ("FaceName", c_wchar * LF_FACESIZE)
    ]


def setFont():
    handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    font = CONSOLE_FONT_INFOEX()
    font.cbSize = sizeof(CONSOLE_FONT_INFOEX)

    windll.kernel32.GetCurrentConsoleFontEx(
        handle,
        c_bool(False),
        pointer(font))

    # font.cbSize = .sizeof(CONSOLE_FONT_INFOEX)
    # font.nFont = 12
    # font.dwFontSize.X = 11
    # font.dwFontSize.Y = 18
    # font.FontFamily = 54
    # font.FontWeight = 400
    # font.FaceName = "Lucida Console"

    if platform.platform().startswith('Windows-10'):
        font.FaceName = "黑体"
    else:
        font.FaceName = "新宋体"

    windll.kernel32.SetCurrentConsoleFontEx(
        handle,
        c_long(False),
        pointer(font))


class SMALL_RECT(Structure):
    _fields_ = [
        ("Left", c_short),
        ("Top", c_short),
        ("Right", c_short),
        ("Bottom", c_short)
    ]


class CONSOLE_SCREEN_BUFFER_INFOEX(Structure):
    _fields_ = [
        ("cbSize", c_ulong),  # 4
        ("dwSize", COORD),  # 2+2
        ("dwCursorPosition", COORD),  # 2+2
        ("wAttributes", c_ushort),  # 4
        ("srWindow", SMALL_RECT),  # 8
        ("dwMaximumWindowSize", COORD),  # 2+2
        ("wPopupAttributes", c_ushort),  # 4
        ("bFullscreenSupported", c_bool),  # x4
        ("ColorTable", c_ulong * 16)  # 4x16 = 64      32
    ]


class CONSOLE_SCREEN_BUFFER_INFO(Structure):
    _fields_ = [
        ("dwSize", COORD),  # 2+2
        ("dwCursorPosition", COORD),  # 2+2
        ("wAttributes", c_ushort),  # 4
        ("srWindow", SMALL_RECT),  # 8
        ("dwMaximumWindowSize", COORD),  # 2+2
    ]


def setBuffer():
    handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    width = 110
    height = 40

    rect = SMALL_RECT()
    rect.Left = 0
    rect.Right = width - 1
    rect.Top = 0
    rect.Bottom = height - 1

    windll.kernel32.SetConsoleWindowInfo(
        handle,
        c_bool(True),
        pointer(rect))
    print('Last: ' + str(windll.kernel32.GetLastError()))

    ###

    bufferSize = COORD(width, height)

    windll.kernel32.SetConsoleScreenBufferSize(
        handle,
        pointer(bufferSize))
    ret = windll.kernel32.GetLastError()
    print('Last: ' + str(ret))


if __name__ == "__main__":
    setBuffer()
