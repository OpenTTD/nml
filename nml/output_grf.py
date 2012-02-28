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

# Some constants for the 'info' byte
INFO_RGB    = 1
INFO_ALPHA  = 2
INFO_PAL    = 4
INFO_TILE   = 8
INFO_NOCROP = 0x40

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
        elif type == 0xFD:
            # Real sprite, this means no data is written to the data section
            # This call is still needed to open 'output mode'
            assert size == 0
            output_base.BinaryOutputBase.start_sprite(self, 9)
            self.print_dword(4)
            self.print_byte(0xfd)
            self.print_dword(self.sprite_num)
        else:
            assert False, "Unexpected info byte encountered."

    def print_sprite(self, sprite_list):
        """
        @param sprite_list: List of non-empty real sprites for various bit depths / zoom levels
        @type sprite_list: C{list} of L{RealSprite}
        """
        self.start_sprite(0, 0xFD)
        for sprite in sprite_list:
            self.print_single_sprite(sprite)
        self.end_sprite()

    def print_single_sprite(self, sprite_info):
        # Open file
        if not os.path.exists(sprite_info.file.value):
            raise generic.ImageError("File doesn't exist", sprite_info.file.value)
        im = Image.open(sprite_info.file.value)

        # Check that file type matches bit depth, and load palette if applicable
        if sprite_info.bit_depth == 8:
            if im.mode != "P":
                raise generic.ImageError("8bpp image does not have a palette", sprite_info.file.value)
            im_pal = palette.validate_palette(im, sprite_info.file.value)
            info_byte = INFO_PAL
        else:
            if im.mode not in ("RGB", "RGBA"):
                raise generic.ImageError("32bpp image is not a full colour RGB(A) image.", sprite_info.file.value)
            im_pal = None
            info_byte = INFO_RGB
            if im.mode == "RGBA": info_byte |= INFO_ALPHA
        info_byte |= sprite_info.compression.value

        # Select region of image bounded by x/ypos and x/ysize
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        (im_width, im_height) = im.size
        if x + size_x > im_width or y + size_y > im_height:
            raise generic.ScriptError("Read beyond bounds of image file '%s'" % sprite_info.file.value, sprite_info.file.pos)
        sprite = im.crop((x, y, x + size_x, y + size_y))

        # Check for white pixels; those that cause "artefacts" when shading
        if sprite_info.bit_depth == 8:
            white_pixels = 0
            for p in sprite.getdata():
                if p == 255:
                    white_pixels += 1
            if white_pixels != 0:
                pixels = sprite.size[0] * sprite.size[1]
                pos = generic.PixelPosition(sprite_info.file.value, x, y)
                generic.print_warning("%i of %i pixels (%i%%) are pure white" % (white_pixels, pixels, white_pixels * 100 / pixels), pos)
        self.wsprite(sprite, sprite_info.xrel.value, sprite_info.yrel.value, info_byte, sprite_info.zoom_level, im_pal)

    def print_empty_realsprite(self):
        self.start_sprite(1)
        self.print_byte(0, True)
        self.end_sprite()

    def wsprite_header(self, sprite, size, xoffset, yoffset, info, zoom_level):
        size_x, size_y = sprite.size
        self._expected_count += size + 18
        self.print_dword(self.sprite_num, False)
        self.print_dword(size + 10, False)
        self.print_byte(info, False)
        self.print_byte(zoom_level, False)
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
        data_str = ''.join(chr(c) for pixel in data for c in pixel)
        if self.compress_grf:
            lz = lz77.LZ77(data_str)
            stream = lz.encode()
        else:
            stream = self.fakecompress(data_str)
        return stream

    def wsprite_encoderegular(self, sprite, data, data_len, xoffset, yoffset, info, zoom_level):
        chunked = info & INFO_TILE != 0
        size = len(data) * len(data[0]) # Size * bpp
        if chunked:
            size += 4
        self.wsprite_header(sprite, size, xoffset, yoffset, info, zoom_level)
        if chunked:
            self.print_dword(data_len, False)
        for pixel in data:
            for c in pixel:
                self.print_byte(ord(c), False)

    def sprite_encode_tile(self, sprite, data, has_alpha = True, long_format = False):
        size_x, size_y = sprite.size

        # There are basically four different encoding configurations here,
        # but just two variables. If the width of the sprite is more than
        # 256, then the chunk could be 'out of bounds' and thus the long
        # chunk format is used. If the sprite is more than 65536 bytes,
        # then the offsets might not fit and the long format method is
        # used. The latter is enabled via recursion if it's needed.
        long_chunk = size_x > 256
        max_chunk_len = 0x7fff if long_chunk else 0x7f
        trans_len = 0xffff if long_chunk else 0xff
        data_output = []
        offsets = size_y * [0]
        for y in range(size_y):
            offsets[y] = sum(len(x) for x in data_output) + 2 * size_y
            row_data = data[y*size_x : (y+1)*size_x]

            line_parts = []
            x1 = 0
            while x1 < size_x:
                while has_alpha and x1 < size_x and row_data[x1][-1] == 0:
                    x1 += 1
                x2 = x1 + 1
                while has_alpha and x2 < size_x and row_data[x2][-1] != 0:
                    x2 += 1
                if x1 < size_x:
                    line_parts.append((x1, x2))
                x1 = x2

            if len(line_parts) == 0:
                # Completely transparant line
                if long_chunk:
                    data_output.append([0, 0x80, 0, 0])
                else:
                    data_output.append([0x80, 0])
                continue

            for idx, part in enumerate(line_parts):
                x1, x2 = part
                last_mask = 0x80 if idx == len(line_parts) - 1 else 0
                chunk_len = x2 - x1
                assert chunk_len < max_chunk_len
                if long_chunk:
                    data_output.append([chunk_len & 0xFF,
                                       (chunk_len >> 8) | last_mask,
                                       x1 & 0xFF,
                                       x1 >> 8])
                else:
                    data_output.append([chunk_len | last_mask, x1])
                data_output.extend(row_data[x1 : x2])

        output = []
        for offset in offsets:
            output.append([offset & 0xFF, (offset >> 8) & 0xFF])
            if long_format:
                output.append([(offset >> 16) & 0xFF, (offset >> 24) & 0xFF])
        output += data_output
        if sum(len(x) for x in data_output) > 65535 and not long_format:
            # Recurse into the long format if that's possible.
            return self.sprite_encode_tile(sprite, data, has_alpha, True)
        return output

    def crop_sprite(self, sprite, xoffset, yoffset, info):
        data = list(sprite.getdata())
        size_x, size_y = sprite.size

        def is_transparant(p, info):
            if (info & INFO_PAL) != 0:
                return p == 0
            if (info & INFO_ALPHA) != 0:
                return p[-1] == 0
            return False

        #Crop the top of the sprite
        y = 0
        while y < size_y:
            x = 0
            while x < size_x:
                if not is_transparant(data[y * size_x + x], info): break
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
                if not is_transparant(data[y * size_x + x], info): break
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
                if not is_transparant(data[y * size_x + x], info): break
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
                if not is_transparant(data[y * size_x + x], info): break
                y += 1
            if y != size_y: break
            x -= 1
        if x != size_x - 1:
            sprite = sprite.crop((0, 0, x + 1, size_y))
        return (sprite, xoffset, yoffset)

    def wsprite(self, sprite, xoffset, yoffset, info, zoom_level, orig_pal):
        if self.crop_sprites and (info & INFO_NOCROP == 0):
            all_blue = True
            if (info & INFO_PAL) != 0:
                all_blue = all([p == 0 for p in sprite.getdata()])
            elif (info & INFO_ALPHA) != 0:
                all_blue = all([p[-1] == 0 for p in sprite.getdata()])
            else:
                all_blue = False
            if all_blue:
                sprite = sprite.crop((0, 0, 1, 1))
                xoffset = 0
                yoffset = 0
            else:
                sprite, xoffset, yoffset = self.crop_sprite(sprite, xoffset, yoffset, info)

        # Palconvert if needed
        if (info & INFO_PAL) != 0 and orig_pal == "WIN":
            if self.palette == "DOS":
                data = [palmap_w2d[x] for x in data]
                
        data = list(sprite.getdata())
        if not isinstance(data[0], tuple):
            # Palette data isn't a tuple, but rgb(a) is. Convert the former to a tuple also
            data = [(d, ) for d in data]

        compressed_data = self.sprite_compress(data)
        data_len = len(data)
        has_alpha = ((info & INFO_RGB) != 0 and (info & INFO_ALPHA) != 0) or (info & INFO_PAL) != 0
        # Try tile compression, and see if it results in a smaller file size
        tile_data = self.sprite_encode_tile(sprite, data, has_alpha)
        if tile_data is not None:
            tile_compressed_data = self.sprite_compress(tile_data)
            # Tile compression adds another 4 bytes for the uncompressed chunked data in the header
            if len(tile_compressed_data) + 4 < len(compressed_data):
                info |= INFO_TILE
                compressed_data = tile_compressed_data
                data_len = len(tile_data)
        self.wsprite_encoderegular(sprite, compressed_data, data_len, xoffset, yoffset, info, zoom_level)

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
