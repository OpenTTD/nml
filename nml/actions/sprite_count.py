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


class SpriteCountAction:
    def __init__(self, count):
        self.count = count

    def prepare_output(self, sprite_num):
        assert sprite_num == 0

    def write(self, file):
        file.start_sprite(4)
        file.print_dword(self.count)
        file.newline()
        file.end_sprite()
