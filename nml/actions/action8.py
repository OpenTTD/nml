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

from nml import grfstrings
from nml.actions import base_action

class Action8(base_action.BaseAction):
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description

    def write(self, file):
        name = grfstrings.get_translation(self.name)
        desc = grfstrings.get_translation(self.description)
        size = 6 + grfstrings.get_string_size(name) + grfstrings.get_string_size(desc)
        file.start_sprite(size)
        file.print_bytex(8)
        file.print_bytex(7)
        file.print_string(self.grfid.value, False, True)
        file.print_string(name)
        file.print_string(desc)
        file.end_sprite()

    def skip_action7(self):
        return False
