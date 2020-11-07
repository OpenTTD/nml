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

from nml.actions import base_action


class ActionE(base_action.BaseAction):
    def __init__(self, grfid_list):
        self.grfid_list = grfid_list

    def write(self, file):
        size = 2 + 4 * len(self.grfid_list)
        file.start_sprite(size)
        file.print_bytex(0x0E)
        file.print_byte(len(self.grfid_list))
        for grfid in self.grfid_list:
            file.newline()
            file.print_dwordx(grfid)
        file.newline()
        file.end_sprite()


def parse_deactivate_block(block):
    return [ActionE(block.grfid_list)]
