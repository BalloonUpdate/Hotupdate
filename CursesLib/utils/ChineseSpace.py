import platform


def insertSpaceBehindChinese(text, spaceChar=' '):
    def findChinese(start, word):
        index = 0

        for ch in word[start:]:
            if '\u4e00' <= ch <= '\u9fff':
                return index + startAt
            index += 1
        return -1

    startAt = 0

    while True:
        pos = findChinese(startAt, text)

        if pos != -1:
            text = text[:pos + 1] + spaceChar + text[pos + 1:]

            startAt = pos + 1
        else:
            break

    return text


def smartStretch(text, spaceChar=' '):
    # win10平台+实机环境
    if platform.platform().startswith('Windows-10'):
        return insertSpaceBehindChinese(text, spaceChar)
    return text


def split(text, width):
    """将单行字符串分隔成多行"""
    lines = []
    temp = ''
    for ch in text:
        if ch == '\n' or ch == '\r\n':
            lines.append(temp)
            temp = ''
        else:
            temp += ch

        if len(temp) >= width:
            lines.append(temp)
            temp = ''
    if len(temp) > 0:
        lines.append(temp)
    return lines