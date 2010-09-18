import codecs
from nml import output_base

class OutputNML(output_base.OutputBase):
    """
    Class for outputting NML.
    """
    def __init__(self, filename):
        output_base.OutputBase.__init__(self, filename)

    def open(self):
        self.file = codecs.open(self.filename, 'w', 'utf-8')

    def close(self):
        self.file.close()


    def write(self, text):
        self.file.write(text)

    def newline(self):
        self.file.write('\n')
