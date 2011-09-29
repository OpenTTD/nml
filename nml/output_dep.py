# -*- coding: utf-8 -*-
import codecs
from nml import generic, grfstrings, output_base

class OutputDEP(output_base.OutputBase):
    """
    Class for output to a dependency file in makefile format.
    """
    def __init__(self, filename, grf_filename):
        output_base.OutputBase.__init__(self, filename)
        self.grf_filename = grf_filename

    def open_file(self):
        return codecs.open(self.filename, 'w', 'utf-8')

    def write(self, text):
        self.file.write(self.grf_filename + ': ' + text + '\n')

    def skip_sprite_checks(self):
        return True
