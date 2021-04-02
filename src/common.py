import sys

inDev = not getattr(sys, 'frozen', False)

devDirectory = 'debug-workdir'
