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
        self.data_output = []
        self.sprite_output = []
        # sprite_num is deliberately off-by-one because it is used as an
        # id between data and sprite section. For the sprite section an id
        # of 0 is invalid (means end of sprites), and for a non-NewGRF GRF
        # the first sprite is a real sprite.
        self.sprite_num = 1

    def open_file(self):
        return open(self.filename, 'wb')

    def pre_close(self):
        output_base.BinaryOutputBase.pre_close(self)

        #add end-of-chunks
        self._in_sprite = True
        self.print_dword(0, True)
        self.print_dword(0, False)
        self._in_sprite = False

        #add header
        for c in [ '\x00', '\x00', 'G', 'R', 'F', '\x82', '\x0D', '\x0A', '\x1A', '\x0A' ]:
            self.file.write(c)
        size = len(self.data_output) + 1
        self.file.write(chr(size & 0xFF))
        self.file.write(chr((size >> 8) & 0xFF))
        self.file.write(chr((size >> 16) & 0xFF))
        self.file.write(chr(size >> 24))

        self.file.write('\x00') #no compression

        #add data section, and then the sprite section
        for c in self.data_output:
            self.file.write(c)
        for c in self.sprite_output:
            self.file.write(c)

    def wb(self, byte, data = True):
        if data:
            self.data_output.append(chr(byte))
        else:
            self.sprite_output.append(chr(byte))

    def print_byte(self, value, data = True):
        value = self.prepare_byte(value)
        self.wb(value, data)

    def print_bytex(self, value, data = True, pretty_print = None):
        self.print_byte(value, data)

    def print_word(self, value, data = True):
        value = self.prepare_word(value)
        self.wb(value & 0xFF, data)
        self.wb(value >> 8, data)

    def print_wordx(self, value, data = True):
        self.print_word(value, data)

    def print_dword(self, value, data = True):
        value = self.prepare_dword(value)
        self.wb(value & 0xFF, data)
        self.wb((value >> 8) & 0xFF, data)
        self.wb((value >> 16) & 0xFF, data)
        self.wb(value >> 24, data)

    def print_dwordx(self, value, data = True):
        self.print_dword(value, data)

    def _print_utf8(self, char, data = True):
        for c in unichr(char).encode('utf8'):
            self.print_byte(ord(c), data)

    def print_string(self, value, final_zero = True, force_ascii = False, data = True):
        if not grfstrings.is_ascii_string(value):
            if force_ascii:
                raise generic.ScriptError("Expected ascii string but got a unicode string")
            self.print_byte(0xC3, data)
            self.print_byte(0x9E, data)
        i = 0
        while i < len(value):
            if value[i] == '\\':
                if value[i+1] in ('\\', 'n', '"'):
                    self.print_byte(ord(value[i+1]), data)
                    i += 2
                elif value[i+1] == 'U':
                    self._print_utf8(int(value[i+2:i+6], 16), data)
                    i += 6
                else:
                    self.print_byte(int(value[i+1:i+3], 16), data)
                    i += 3
            else:
                self._print_utf8(ord(value[i]), data)
                i += 1
        if final_zero: self.print_byte(0, data)

    def newline(self, msg = "", prefix = "\t"):
        pass

    def comment(self, msg):
        pass

    def start_sprite(self, size, type = 0xFF, data = True):
        if type == 0xFF:
            output_base.BinaryOutputBase.start_sprite(self, size + 5)
            if not data:
                # The compression byte (=type) is counted when in the sprite section,
                # however since this is a sound we need to emit the sprite number as well.
                self.print_dword(self.sprite_num, data)
                self._byte_count -= 3
            self.print_dword(size, data)
            self.print_byte(type, data)
        else:
            output_base.BinaryOutputBase.start_sprite(self, size + 9)
            self.print_dword(self.sprite_num, False)
            self.print_dword(size + 1, False)
            self.print_byte(type, False)

            self.print_dword(4)
            self.print_byte(0xfd)
            self.print_dword(self.sprite_num)
            self._byte_count -= 9

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
        (im_width, im_height) = im.size
        if x + size_x > im_width or y + size_y > im_height:
            raise generic.ScriptError("Read beyond bounds of image file '%s'" % sprite_info.file.value, sprite_info.file.pos)
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
        self.print_byte(0, True)
        self.end_sprite()

    def wsprite_header(self, sprite, size, xoffset, yoffset, compression):
        size_x, size_y = sprite.size
        self.start_sprite(size + 9, compression & ~1 | 0x04) # Determine Type, remove bit 0, TODO
        self.print_byte(0, False) # Zoom, TODO
        self.print_word(size_y, False)
        self.print_word(size_x, False)
        self.print_word(xoffset, False)
        self.print_word(yoffset, False)

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
        chunked = compression & 8 != 0
        size = len(data)
        if chunked:
            size += 4
        self.wsprite_header(sprite, size, xoffset, yoffset, compression)
        if chunked:
            self.print_dword(data_len, False)
        for c in data:
            self.print_byte(ord(c), False)
        self.end_sprite()

    def sprite_encode_tile(self, sprite, data, long_format = False):
        size_x, size_y = sprite.size

        # There are basically four different encoding configurations here,
        # but just two variables. If the width of the sprite is more than
        # 256, then the chunk could be 'out of bounds' and thus the long
        # chunk format is used. If the sprite is more than 65536 bytes,
        # then the offsets might not fit and the long format method is
        # used. The latter is enabled via recursion if it's needed.
        long_chunk = size_x > 256
        chunk_len = 0x7fff if long_chunk else 0x7f
        trans_len = 0xffff if long_chunk else 0xff
        data_output = []
        offsets = size_y * [0]
        for y in range(size_y):
            offsets[y] = len(data_output) + 2 * size_y
            row_data = data[y*size_x : (y+1)*size_x]
            last = size_x - 1
            while last >= 0 and row_data[last] == 0: last -= 1
            if last == -1:
                data_output += [0, 0x80, 0, 0] if long_chunk else [0x80, 0]
                continue
            x1 = 0
            while x1 < size_x and row_data[x1] == 0:
                x1 += 1

            if x1 == size_x:
                # Completely transparant line
                data_output.append(0)
                data_output.append(0)
                if long_chunk:
                    data_output.append(0)
                    data_output.append(0)
                continue

            x2 = size_x
            while row_data[x2 - 1] == 0:
                x2 -= 1

            # Chunk can start maximum at trans_len and has maximum width of chunk_len
            if x2 - trans_len > chunk_len:
                return None
            if x2 - x1 > chunk_len:
                #too large to fit in one chunk, so split it up.
                if long_chunk:
                    data_output.append(0xFF)
                    data_output.append(0x7F)
                    data_output.append(x1 & 0xFF)
                    data_output.append(x1 >> 8)
                else:
                    data_output.append(0x7F)
                    data_output.append(x1)
                data_output += row_data[x1 : x1 + chunk_len]
                x1 += chunk_len
            if long_chunk:
                data_output.append((x2 - x1) & 0xFF)
                data_output.append((x2 - x1) >> 8 | 0x80)
                data_output.append(x1 & 0xFF)
                data_output.append(x1 >> 8)
            else:
                data_output.append((x2 - x1) | 0x80)
                data_output.append(x1)
            data_output += row_data[x1 : x2]
        output = []
        for offset in offsets:
            output.append(offset & 0xFF)
            output.append((offset >> 8) & 0xFF)
            if long_format:
                output.append((offset >> 16) & 0xFF)
                output.append((offset >> 24) & 0xFF)
        output += data_output
        if len(output) > 65535 and not long_format:
            # Recurse into the long format if that's possible.
            return self.sprite_encode_tile(sprite, data, True)
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
            # Tile compression adds another 4 bytes for the uncompressed chunked data in the header
            if len(tile_compressed_data) + 4 < len(compressed_data):
                compression |= 8
                compressed_data = tile_compressed_data
                data_len = len(tile_data)
        self.wsprite_encoderegular(sprite, compressed_data, data_len, xoffset, yoffset, compression)

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)
        total = 3 + len(name) + 1 + size

        self.start_sprite(total, 0xff, False)
        self.print_byte(0xff, False)
        self.print_byte(len(name), False)
        self.print_string(name, force_ascii = True, final_zero = True, data = False)  # ASCII filenames seems sufficient.
        fp = open(filename, 'rb')
        while True:
            data = fp.read(1024)
            if len(data) == 0: break
            for d in data:
                self.print_byte(ord(d), False)
        fp.close()

        self.print_dword(4)
        self.print_byte(0xfd)
        self.print_dword(self.sprite_num)
        self._byte_count -= 9
        self.end_sprite()

    def end_sprite(self):
        output_base.BinaryOutputBase.end_sprite(self)
        self.sprite_num += 1
