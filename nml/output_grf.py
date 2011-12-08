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

import os
from nml import generic, palette, output_base, lz77, grfstrings
from nml.actions.real_sprite import palmap_w2d

try:
    import Image
except ImportError:
    pass

class OutputGRF(output_base.BinaryOutputBase):
    def __init__(self, filename, compress_grf, crop_sprites):
        output_base.BinaryOutputBase.__init__(self, filename)
        self.compress_grf = compress_grf
        self.crop_sprites = crop_sprites

    def open_file(self):
        return open(self.filename, 'wb')

    def pre_close(self):
        output_base.BinaryOutputBase.pre_close(self)
        #terminate with 6 zero bytes (zero-size sprite + checksum)
        i = 0
        while i < 6:
            self.wb(0)
            i += 1

    def wb(self, byte):
        self.file.write(chr(byte))

    def print_byte(self, value):
        value = self.prepare_byte(value)
        self.wb(value)

    def print_bytex(self, value, pretty_print = None):
        self.print_byte(value)

    def print_word(self, value):
        value = self.prepare_word(value)
        self.wb(value & 0xFF)
        self.wb(value >> 8)

    def print_wordx(self, value):
        self.print_word(value)

    def print_dword(self, value):
        value = self.prepare_dword(value)
        self.wb(value & 0xFF)
        self.wb((value >> 8) & 0xFF)
        self.wb((value >> 16) & 0xFF)
        self.wb(value >> 24)

    def print_dwordx(self, value):
        self.print_dword(value)

    def _print_utf8(self, char):
        for c in unichr(char).encode('utf8'):
            self.print_byte(ord(c))

    def print_string(self, value, final_zero = True, force_ascii = False):
        if not grfstrings.is_ascii_string(value):
            if force_ascii:
                raise generic.ScriptError("Expected ascii string but got a unicode string")
            self.print_byte(0xC3)
            self.print_byte(0x9E)
        i = 0
        while i < len(value):
            if value[i] == '\\':
                if value[i+1] in ('\\', 'n', '"'):
                    self.print_byte(ord(value[i+1]))
                    i += 2
                elif value[i+1] == 'U':
                    self._print_utf8(int(value[i+2:i+6], 16))
                    i += 6
                else:
                    self.print_byte(int(value[i+1:i+3], 16))
                    i += 3
            else:
                self._print_utf8(ord(value[i]))
                i += 1
        if final_zero: self.print_byte(0)

    def newline(self, msg = "", prefix = "\t"):
        pass

    def comment(self, msg):
        pass

    def start_sprite(self, size, type = 0xFF):
        #The compression byte (=type) is counted when *not* 0xFF
        size += (type != 0xFF)
        output_base.BinaryOutputBase.start_sprite(self, size + 2)
        self.print_word(size)
        self.print_byte(type)
        if type == 0xFF: self._byte_count -= 1

    def print_sprite(self, sprite_info):
        if not os.path.exists(sprite_info.file.value):
            raise generic.ImageError("File doesn't exist", sprite_info.file.value)
        im = Image.open(sprite_info.file.value)
        if im.mode != "P":
            raise generic.ImageError("image does not have a palette", sprite_info.file.value)
        im_pal = palette.validate_palette(im, sprite_info.file.value)
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        sprite = im.crop((x, y, x + size_x, y + size_y))

        # Check for white pixels; those that cause "artefacts" when shading
        white_pixels = 0
        for p in sprite.getdata():
            if p == 255:
                white_pixels += 1
        if white_pixels != 0:
            pixels = sprite.size[0] * sprite.size[1]
            pos = generic.PixelPosition(sprite_info.file.value, x, y)
            generic.print_warning("%i of %i pixels (%i%%) are pure white" % (white_pixels, pixels, white_pixels * 100 / pixels), pos)
        self.wsprite(sprite, sprite_info.xrel.value, sprite_info.yrel.value, sprite_info.compression.value, im_pal)

    def print_empty_realsprite(self):
        self.start_sprite(1)
        self.print_byte(0)
        self.end_sprite()

    def wsprite_header(self, sprite, size, xoffset, yoffset, compression):
        size_x, size_y = sprite.size
        self.start_sprite(size + 7, compression)
        self.print_byte(size_y)
        self.print_word(size_x)
        self.print_word(xoffset)
        self.print_word(yoffset)

    def fakecompress(self, data):
        i = 0
        output = ""
        while i < len(data):
            l = min(len(data) - i, 127)
            output += chr(l)
            while l > 0:
                output += data[i]
                i += 1
                l -= 1
        return output

    def sprite_compress(self, data):
        data_str = ''.join(chr(c) for c in data)
        if self.compress_grf:
            lz = lz77.LZ77(data_str)
            stream = lz.encode()
        else:
            stream = self.fakecompress(data_str)
        return stream

    def wsprite_encoderegular(self, sprite, data, data_len, xoffset, yoffset, compression):
        self.wsprite_header(sprite, data_len, xoffset, yoffset, compression)
        for c in data:
            self.print_byte(ord(c))
        #make up for the difference in byte count
        self._byte_count += data_len - len(data)
        self.end_sprite()

    def sprite_encode_tile(self, sprite, data):
        size_x, size_y = sprite.size
        if size_y > 255: raise generic.ScriptError("sprites higher than 255px are not supported")
        data_output = []
        offsets = size_y * [0]
        for y in range(size_y):
            offsets[y] = len(data_output) + 2 * size_y
            row_data = data[y*size_x : (y+1)*size_x]
            last = size_x - 1
            while last >= 0 and row_data[last] == 0: last -= 1
            if last == -1:
                data_output += [0x80, 0]
                continue
            x1 = 0
            while x1 < size_x and row_data[x1] == 0:
                x1 += 1

            if x1 == size_x:
                # Completely transparant line
                data_output.append(0)
                data_output.append(0)
                continue

            x2 = size_x
            while row_data[x2 - 1] == 0:
                x2 -= 1

            # Chunk can start maximu at 0xFF and has maximum width of 0x7F
            if x2 - 0xFF > 0x7F:
                return None
            if x2 - x1 > 0x7F:
                #too large to fit in one chunk, so split it up.
                data_output.append(0x7F)
                data_output.append(x1)
                data_output += row_data[x1 : x1 + 0x7F]
                x1 += 0x7F
            data_output.append((x2 - x1) | 0x80)
            data_output.append(x1)
            data_output += row_data[x1 : x2]
        output = []
        for offset in offsets:
            output.append(offset & 0xFF)
            output.append(offset >> 8)
        output += data_output
        return output

    def crop_sprite(self, sprite, xoffset, yoffset):
        data = list(sprite.getdata())
        size_x, size_y = sprite.size

        #Crop the top of the sprite
        y = 0
        while y < size_y:
            x = 0
            while x < size_x:
                if data[y * size_x + x] != 0: break
                x += 1
            if x != size_x: break
            y += 1
        if y != 0:
            yoffset += y
            sprite = sprite.crop((0, y, size_x, size_y))
            data = list(sprite.getdata())
            size_y -= y

        #Crop the bottom of the sprite
        y = size_y - 1
        while y >= 0:
            x = 0
            while x < size_x:
                if data[y * size_x + x] != 0: break
                x += 1
            if x != size_x: break
            y -= 1
        if y != size_y - 1:
            sprite = sprite.crop((0, 0, size_x, y + 1))
            data = list(sprite.getdata())
            size_y = y + 1

        #Crop the left of the sprite
        x = 0
        while x < size_x:
            y = 0
            while y < size_y:
                if data[y * size_x + x] != 0: break
                y += 1
            if y != size_y: break
            x += 1
        if x != 0:
            xoffset += x
            sprite = sprite.crop((x, 0, size_x, size_y))
            data = list(sprite.getdata())
            size_x -= x

        #Crop the right of the sprite
        x = size_x - 1
        while x >= 0:
            y = 0
            while y < size_y:
                if data[y * size_x + x] != 0: break
                y += 1
            if y != size_y: break
            x -= 1
        if x != size_x - 1:
            sprite = sprite.crop((0, 0, x + 1, size_y))
        return (sprite, xoffset, yoffset)

    def wsprite(self, sprite, xoffset, yoffset, compression, orig_pal):
        if self.crop_sprites and (compression & 0x40 == 0):
            all_blue = True
            for p in sprite.getdata():
                if p != 0:
                    all_blue = False
                    break
            if all_blue:
                sprite = sprite.crop((0, 0, 1, 1))
                xoffset = 0
                yoffset = 0
            else:
                sprite, xoffset, yoffset = self.crop_sprite(sprite, xoffset, yoffset)
        data = list(sprite.getdata())
        if orig_pal == "WIN":
            if self.palette == "DOS":
                data = [palmap_w2d[x] for x in data]
        compressed_data = self.sprite_compress(data)
        data_len = len(data)
        tile_data = self.sprite_encode_tile(sprite, data)
        if tile_data is not None:
            tile_compressed_data = self.sprite_compress(tile_data) 
            if len(tile_compressed_data) < len(compressed_data):
                compression |= 8
                compressed_data = tile_compressed_data
                data_len = len(tile_data)
        self.wsprite_encoderegular(sprite, compressed_data, data_len, xoffset, yoffset, compression)

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)
        total = 2 + len(name) + 1 + size
        self.start_sprite(total)
        self.print_bytex(0xff)
        self.print_bytex(len(name))
        self.print_string(name, force_ascii = True, final_zero = True)  # ASCII filenames seems sufficient.
        fp = open(filename, 'rb')
        while True:
            data = fp.read(1024)
            if len(data) == 0: break
            for d in data:
                self.print_bytex(ord(d))
        fp.close()
        self.end_sprite()

