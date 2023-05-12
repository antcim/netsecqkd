import sys

class Logger(object):

    def __init__(self, file):
        self.terminal = sys.stdout
        self.log = open(file, "a")

    def write(self, msg):
        self.terminal.write(msg)
        self.log.write(msg)

    def flush(self):
        pass
