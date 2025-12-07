# SPDX-License-Identifier: GPL-2.0-or-later

# -*- coding: utf-8 -*-
from nml import output_base


class OutputDEP(output_base.TextOutputBase):
    """
    Class for output to a dependency file in makefile format.
    """

    def __init__(self, filename, grf_filename):
        output_base.TextOutputBase.__init__(self, filename)
        self.grf_filename = grf_filename

    def open_file(self):
        return open(self.filename, "w", encoding="utf-8")

    def write(self, text):
        self.file.write(self.grf_filename + ": " + text + "\n")

    def skip_sprite_checks(self):
        return True
