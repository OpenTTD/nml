import codecs

class OutputNML(object):
    """
    Class for outputting NML.

    @ivar filename: Filename
    @type filename: C{str}

    @ivar file: File handle if opened.
    @type file: C{file} or C{None}
    """
    def __init__(self, filename):
        self.filename = filename
        self.file = None

        self.open()

    def open(self):
        self.file = codecs.open(self.filename, 'w', 'utf-8')

    def close(self):
        self.file.close()


    def write(self, text):
        self.file.write(text)

    def newline(self):
        self.file.write('\n')
