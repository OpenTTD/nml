# SPDX-License-Identifier: GPL-2.0-or-later

from nml import output_base


class OutputNML(output_base.TextOutputBase):
    """
    Class for outputting NML.
    """

    def __init__(self, filename):
        output_base.TextOutputBase.__init__(self, filename)

    def open_file(self):
        return open(self.filename, "w", encoding="utf-8")

    def write(self, text):
        self.file.write(text)

    def newline(self):
        self.file.write("\n")
