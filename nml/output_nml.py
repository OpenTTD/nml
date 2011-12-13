__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

import codecs
from nml import output_base

class OutputNML(output_base.OutputBase):
    """
    Class for outputting NML.
    """
    def __init__(self, filename):
        output_base.OutputBase.__init__(self, filename)

    def open_file(self):
        return codecs.open(self.filename, 'w', 'utf-8')


    def write(self, text):
        self.file.write(text)

    def newline(self):
        self.file.write('\n')
