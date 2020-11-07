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


class Action10(base_action.BaseAction):
    def __init__(self, label):
        self.label = label

    def write(self, file):
        file.start_sprite(2)
        file.print_bytex(0x10)
        file.print_bytex(self.label)
        file.newline()
        file.end_sprite()

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False
