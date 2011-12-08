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

from nml import free_number_list
from nml.actions import base_action

free_parameters = free_number_list.FreeNumberList(list(range(0x7F, 0x3F, -1)))

class Action6(base_action.BaseAction):
    def __init__(self):
        self.modifications = []

    def modify_bytes(self, param, num_bytes, offset):
        self.modifications.append( (param, num_bytes, offset) )

    def write(self, file):
        size = 2 + 5 * len(self.modifications)
        file.start_sprite(size)
        file.print_bytex(6)
        file.newline()
        for mod in self.modifications:
            file.print_bytex(mod[0])
            file.print_bytex(mod[1])
            file.print_bytex(0xFF)
            file.print_wordx(mod[2])
            file.newline()
        file.print_bytex(0xFF)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        return False
