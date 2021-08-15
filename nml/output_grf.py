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

import hashlib
import os

from nml import generic, grfstrings, output_base


class OutputGRF(output_base.BinaryOutputBase):
    def __init__(self, filename):
        output_base.BinaryOutputBase.__init__(self, filename)
        self.encoder = None
        self.sprite_output = output_base.BinaryOutputBase(filename + ".sprite.tmp")
        self.md5 = hashlib.md5()
        # sprite_num is deliberately off-by-one because it is used as an
        # id between data and sprite section. For the sprite section an id
        # of 0 is invalid (means end of sprites), and for a non-NewGRF GRF
        # the first sprite is a real sprite.
        self.sprite_num = 1

    def open_file(self):
        # Remove / unlink the file, most useful for linux systems
        # See also issue #4165
        # If the file happens to be in use or non-existant, ignore
        try:
            os.unlink(self.filename)
        except OSError:
            # Ignore
            pass
        return open(self.filename, "wb")

    def get_md5(self):
        return self.md5.hexdigest()

    def assemble_file(self, real_file):
        # add end-of-chunks
        self.in_sprite = True
        self.print_dword(0)
        self.in_sprite = False
        self.sprite_output.in_sprite = True
        self.sprite_output.print_dword(0)
        self.sprite_output.in_sprite = False

        # add header
        header = bytearray([0x00, 0x00, ord("G"), ord("R"), ord("F"), 0x82, 0x0D, 0x0A, 0x1A, 0x0A])
        size = len(self.file) + 1
        header.append(size & 0xFF)
        header.append((size >> 8) & 0xFF)
        header.append((size >> 16) & 0xFF)
        header.append(size >> 24)
        header.append(0)  # no compression

        header_str = bytes(header)
        real_file.write(header_str)
        self.md5.update(header_str)

        # add data section, and then the sprite section
        real_file.write(self.file)
        self.md5.update(self.file)

        real_file.write(self.sprite_output.file)

    def open(self):
        output_base.BinaryOutputBase.open(self)
        self.sprite_output.open()

    def close(self):
        output_base.BinaryOutputBase.close(self)
        self.sprite_output.discard()

    def _print_utf8(self, char, stream):
        for c in chr(char).encode("utf8"):
            stream.print_byte(c)

    def print_string(self, value, final_zero=True, force_ascii=False, stream=None):
        if stream is None:
            stream = self

        if not grfstrings.is_ascii_string(value):
            if force_ascii:
                raise generic.ScriptError("Expected ascii string but got a unicode string")
            stream.print_byte(0xC3)
            stream.print_byte(0x9E)
        i = 0
        while i < len(value):
            if value[i] == "\\":
                if value[i + 1] in ("\\", '"'):
                    stream.print_byte(ord(value[i + 1]))
                    i += 2
                elif value[i + 1] == "U":
                    self._print_utf8(int(value[i + 2 : i + 6], 16), stream)
                    i += 6
                else:
                    stream.print_byte(int(value[i + 1 : i + 3], 16))
                    i += 3
            else:
                self._print_utf8(ord(value[i]), stream)
                i += 1
        if final_zero:
            stream.print_byte(0)

    def comment(self, msg):
        pass

    def start_sprite(self, size, is_real_sprite=False):
        if is_real_sprite:
            # Real sprite, this means no data is written to the data section
            # This call is still needed to open 'output mode'
            assert size == 0
            output_base.BinaryOutputBase.start_sprite(self, 9)
            self.print_dword(4)
            self.print_byte(0xFD)
            self.print_dword(self.sprite_num)
        else:
            output_base.BinaryOutputBase.start_sprite(self, size + 5)
            self.print_dword(size)
            self.print_byte(0xFF)

    def print_sprite(self, sprite_list):
        """
        @param sprite_list: List of non-empty real sprites for various bit depths / zoom levels
        @type  sprite_list: C{list} of L{RealSprite}
        """
        self.start_sprite(0, True)
        for sprite in sprite_list:
            self.print_single_sprite(sprite)
        self.end_sprite()

    def print_single_sprite(self, sprite_info):
        assert sprite_info.file is not None or sprite_info.mask_file is not None

        # Position for warning messages
        pos_warning = None
        if sprite_info.mask_file is not None:
            pos_warning = sprite_info.mask_file.pos
        elif sprite_info.file is not None:
            pos_warning = sprite_info.file.pos

        size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, warnings = self.encoder.get(
            sprite_info
        )

        for w in warnings:
            generic.print_warning(generic.Warning.GENERIC, w, pos_warning)

        self.sprite_output.start_sprite(len(compressed_data) + 18)
        self.wsprite_header(size_x, size_y, len(compressed_data), xoffset, yoffset, info_byte, sprite_info.zoom_level)
        self.sprite_output.print_data(compressed_data)
        self.sprite_output.end_sprite()

    def print_empty_realsprite(self):
        self.start_sprite(1)
        self.print_byte(0)
        self.end_sprite()

    def wsprite_header(self, size_x, size_y, size, xoffset, yoffset, info, zoom_level):
        self.sprite_output.print_dword(self.sprite_num)
        self.sprite_output.print_dword(size + 10)
        self.sprite_output.print_byte(info)
        self.sprite_output.print_byte(zoom_level)
        self.sprite_output.print_word(size_y)
        self.sprite_output.print_word(size_x)
        self.sprite_output.print_word(xoffset)
        self.sprite_output.print_word(yoffset)

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)

        self.start_sprite(0, True)
        self.sprite_output.start_sprite(8 + 3 + len(name) + 1 + size)

        self.sprite_output.print_dword(self.sprite_num)
        self.sprite_output.print_dword(3 + len(name) + 1 + size)
        self.sprite_output.print_byte(0xFF)
        self.sprite_output.print_byte(0xFF)
        self.sprite_output.print_byte(len(name))
        self.print_string(
            name, force_ascii=True, final_zero=True, stream=self.sprite_output
        )  # ASCII filenames seems sufficient.
        with open(generic.find_file(filename), "rb") as file:
            while True:
                data = file.read(1024)
                if len(data) == 0:
                    break
                for d in data:
                    self.sprite_output.print_byte(d)

        self.sprite_output.end_sprite()
        self.end_sprite()

    def end_sprite(self):
        output_base.BinaryOutputBase.end_sprite(self)
        self.sprite_num += 1
