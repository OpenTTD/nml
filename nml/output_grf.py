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

import array, hashlib, os
from nml import generic, palette, output_base, lz77, grfstrings, spritecache
from nml.actions.real_sprite import translate_w2d

try:
    from PIL import Image
except ImportError:
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

def get_bpp(info):
    bpp = 0
    if (info & INFO_RGB) != 0: bpp += 3
    if (info & INFO_ALPHA) != 0: bpp += 1
    if (info & INFO_PAL) != 0: bpp += 1
    return bpp

def has_transparency(info):
    return (info & (INFO_ALPHA | INFO_PAL)) != 0

def transparency_offset(info):
    """
    Determine which byte within a pixel should be 0 for a pixel to be transparent
    """
    assert has_transparency(info)
    # There is an alpha or palette component, or both, else no transparency at all
    # Pixel is transparent if either:
    # - alpha channel present and 0
    # - palette present and 0, and alpha not present
    # In either case, the pixel is transparent,
    # if byte 3 (with RGB present) or byte 0 (without RGB) is 0
    if (info & INFO_RGB) != 0:
        return 3
    else:
        return 0

class OutputGRF(output_base.BinaryOutputBase):
    def __init__(self, filename, compress_grf, crop_sprites, enable_cache):
        output_base.BinaryOutputBase.__init__(self, filename)
        self.compress_grf = compress_grf
        self.crop_sprites = crop_sprites
        self.enable_cache = enable_cache
        self.sprite_cache = spritecache.SpriteCache(self.filename)
        self.sprite_output = output_base.BinaryOutputBase(filename + ".sprite.tmp")
        self.md5 = hashlib.md5()
        # sprite_num is deliberately off-by-one because it is used as an
        # id between data and sprite section. For the sprite section an id
        # of 0 is invalid (means end of sprites), and for a non-NewGRF GRF
        # the first sprite is a real sprite.
        self.sprite_num = 1
        # Mapping of filenames to cached image files
        self.cached_image_files = {}
        # used_sprite_files (set from main.py) is used to keep track of what files are used and how often
        if self.enable_cache:
            self.sprite_cache.read_cache()

    def open_file(self):
        # Remove / unlink the file, most useful for linux systems
        # See also issue #4165
        # If the file happens to be in use or non-existant, ignore
        try:
            os.unlink(self.filename)
        except OSError:
            pass
        return open(self.filename, 'wb')

    def get_md5(self):
        return self.md5.hexdigest()

    def open_image_file(self, filename):
        """
        Obtain a handle to an image file

        @param filename: Name of the file
        @type  filename: C{str}

        @return: Image file
        @rtype:  L{Image}
        """
        assert filename in self.used_sprite_files
        if filename in self.cached_image_files:
            im = self.cached_image_files[filename]
        else:
            im = Image.open(generic.find_file(filename))
            self.cached_image_files[filename] = im
        self.mark_image_file_used(filename)
        return im

    def mark_image_file_used(self, filename):
        """
        Indicate that an image file is being used, so the internal book-keeping can be updated

        @param filename: Name of the file
        @type  filename: C{str}
        """
        assert filename in self.used_sprite_files
        self.used_sprite_files[filename] -= 1
        if self.used_sprite_files[filename] == 0 and filename in self.cached_image_files:
            # Delete from dictionary if it exists, then data will be freed when it goes out of scope
            del self.cached_image_files[filename]

    def assemble_file(self, real_file):
        # Verify that image file counts were correct
        assert not self.cached_image_files, "Invalid sprite file cache"
        # all values should be 0 at this point
        assert not any(self.used_sprite_files.values()), "Invalid sprite file cache"

        #add end-of-chunks
        self.in_sprite = True
        self.print_dword(0)
        self.in_sprite = False
        self.sprite_output.in_sprite = True
        self.sprite_output.print_dword(0)
        self.sprite_output.in_sprite = False

        #add header
        header = bytearray([0x00, 0x00, ord('G'), ord('R'), ord('F'), 0x82, 0x0D, 0x0A, 0x1A, 0x0A])
        size = len(self.file) + 1
        header.append(size & 0xFF)
        header.append((size >> 8) & 0xFF)
        header.append((size >> 16) & 0xFF)
        header.append(size >> 24)
        header.append(0) #no compression

        header_str = bytes(header)
        real_file.write(header_str)
        self.md5.update(header_str)

        #add data section, and then the sprite section
        real_file.write(self.file)
        self.md5.update(self.file)

        real_file.write(self.sprite_output.file)

    def open(self):
        output_base.BinaryOutputBase.open(self)
        self.sprite_output.open()

    def close(self):
        output_base.BinaryOutputBase.close(self)
        self.sprite_output.discard()
        if self.enable_cache:
            self.sprite_cache.write_cache()

    def _print_utf8(self, char, stream):
        for c in chr(char).encode('utf8'):
            stream.print_byte(c)

    def print_string(self, value, final_zero = True, force_ascii = False, stream = None):
        if stream is None:
            stream = self

        if not grfstrings.is_ascii_string(value):
            if force_ascii:
                raise generic.ScriptError("Expected ascii string but got a unicode string")
            stream.print_byte(0xC3)
            stream.print_byte(0x9E)
        i = 0
        while i < len(value):
            if value[i] == '\\':
                if value[i+1] in ('\\', '"'):
                    stream.print_byte(ord(value[i+1]))
                    i += 2
                elif value[i+1] == 'U':
                    self._print_utf8(int(value[i+2:i+6], 16), stream)
                    i += 6
                else:
                    stream.print_byte(int(value[i+1:i+3], 16))
                    i += 3
            else:
                self._print_utf8(ord(value[i]), stream)
                i += 1
        if final_zero: stream.print_byte(0)

    def comment(self, msg):
        pass

    def start_sprite(self, size, type = 0xFF):
        if type == 0xFF:
            output_base.BinaryOutputBase.start_sprite(self, size + 5)
            self.print_dword(size)
            self.print_byte(type)
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
        @type  sprite_list: C{list} of L{RealSprite}
        """
        self.start_sprite(0, 0xFD)
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

        # Try finding the file in the cache
        # Use cache either if files are older, of if cache entry was not present
        # in the loaded cache, and thus written by the current grf (occurs if sprites are duplicated)
        cache_key = sprite_info.get_cache_key(self.crop_sprites)
        cache_item = self.sprite_cache.get_item(cache_key, self.palette)

        in_use = False
        in_old_cache = False
        if cache_item is not None:
            if sprite_info.file is not None: self.mark_image_file_used(sprite_info.file.value)
            if sprite_info.mask_file is not None: self.mark_image_file_used(sprite_info.mask_file.value)

            # Write a sprite from the cached data
            compressed_data, info_byte, crop_rect, warning, in_old_cache, in_use = cache_item

            size_x = sprite_info.xsize.value
            size_y = sprite_info.ysize.value
            xoffset = sprite_info.xrel.value
            yoffset = sprite_info.yrel.value
            if cache_key[-1]: size_x, size_y, xoffset, yoffset = self.recompute_offsets(size_x, size_y, xoffset, yoffset, crop_rect)
        else:
            size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, warning = self.encode_sprite(sprite_info)

        # Store sprite in cache, unless already up-to-date
        if not in_use:
            cache_item = (compressed_data, info_byte, crop_rect, warning, in_old_cache, True)
            self.sprite_cache.add_item(cache_key, self.palette, cache_item)

        if warning is not None:
            if in_old_cache:
                warning = warning + " (cached warning)"
            generic.print_warning(warning, pos_warning)

        self.sprite_output.start_sprite(len(compressed_data) + 18)
        self.wsprite_header(size_x, size_y, len(compressed_data), xoffset, yoffset, info_byte, sprite_info.zoom_level)
        self.sprite_output.print_data(compressed_data)
        self.sprite_output.end_sprite()

    def encode_sprite(self, sprite_info):
        """
        Crop and compress a real sprite.

        @param sprite_info: Sprite meta data
        @type  sprite_info: C{RealSprite}

        @return: size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, warning
        @rtype: C{tuple}
        """

        filename_8bpp = None
        filename_32bpp = None
        if sprite_info.bit_depth == 8:
            filename_8bpp = sprite_info.file
        else:
            filename_32bpp = sprite_info.file
            filename_8bpp = sprite_info.mask_file

        # Get initial info_byte and dimensions from sprite_info.
        # These values will be changed depending on cropping and compression.
        info_byte = sprite_info.compression.value
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        xoffset = sprite_info.xrel.value
        yoffset = sprite_info.yrel.value

        im, mask_im = None, None
        im_mask_pal = None

        # Select region of image bounded by x/ypos and x/ysize
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        if sprite_info.bit_depth == 8 or sprite_info.mask_pos is None:
            mask_x, mask_y = x, y
        else:
            mask_x = sprite_info.mask_pos[0].value
            mask_y = sprite_info.mask_pos[1].value

        # Read and validate image data
        if filename_32bpp is not None:
            im = self.open_image_file(filename_32bpp.value)
            if im.mode not in ("RGB", "RGBA"):
                raise generic.ImageError("32bpp image is not a full colour RGB(A) image.", filename_32bpp.value)
            info_byte |= INFO_RGB
            if im.mode == "RGBA":
                info_byte |= INFO_ALPHA

            (im_width, im_height) = im.size
            if x < 0 or y < 0 or x + size_x > im_width or y + size_y > im_height:
                raise generic.ScriptError("Read beyond bounds of image file '{}'".format(filename_32bpp.value), filename_32bpp.pos)
            sprite = im.crop((x, y, x + size_x, y + size_y))

        warning = None
        if filename_8bpp is not None:
            mask_im = self.open_image_file(filename_8bpp.value)
            if mask_im.mode != "P":
                raise generic.ImageError("8bpp image does not have a palette", filename_8bpp.value)
            im_mask_pal = palette.validate_palette(mask_im, filename_8bpp.value)
            info_byte |= INFO_PAL

            (im_width, im_height) = mask_im.size
            if mask_x < 0 or mask_y < 0 or mask_x + size_x > im_width or mask_y + size_y > im_height:
                raise generic.ScriptError("Read beyond bounds of image file '{}'".format(filename_8bpp.value), filename_8bpp.pos)
            mask_sprite = mask_im.crop((mask_x, mask_y, mask_x + size_x, mask_y + size_y))

            # Check for white pixels; those that cause "artefacts" when shading
            white_pixels = sum(1 for p in mask_sprite.getdata() if p == 255)
            if white_pixels > 0:
                pixels = size_x * size_y
                image_pos = generic.PixelPosition(filename_8bpp.value, x, y)
                warning = "{}: {:d} of {:d} pixels ({:d}%) are pure white".format(str(image_pos), white_pixels, pixels, white_pixels * 100 // pixels)

            mask_sprite_data = self.palconvert(mask_sprite.tostring(), im_mask_pal)

        # Compose pixel information in an array of bytes
        sprite_data = array.array('B')
        if (info_byte & INFO_RGB) != 0 and (info_byte & INFO_PAL) != 0:
            mask_data = array.array('B', mask_sprite_data) # Convert to numeric
            rgb_data = array.array('B', sprite.tostring())
            if (info_byte & INFO_ALPHA) != 0:
                for i in range(len(mask_sprite_data)):
                    sprite_data.extend(rgb_data[4*i:4*(i+1)])
                    sprite_data.append(mask_data[i])
            else:
                for i in range(len(mask_sprite_data)):
                    sprite_data.extend(rgb_data[3*i:3*(i+1)])
                    sprite_data.append(mask_data[i])
        elif (info_byte & INFO_RGB) != 0:
            sprite_data.fromstring(sprite.tostring())
        else:
            sprite_data.fromstring(mask_sprite_data)

        bpp = get_bpp(info_byte)
        assert len(sprite_data) == size_x * size_y * bpp
        if self.crop_sprites and ((info_byte & INFO_NOCROP) == 0):
            sprite_data, crop_rect = self.crop_sprite(sprite_data, size_x, size_y, info_byte, bpp)
            size_x, size_y, xoffset, yoffset = self.recompute_offsets(size_x, size_y, xoffset, yoffset, crop_rect)
        else:
            crop_rect = None
        assert len(sprite_data) == size_x * size_y * bpp

        compressed_data = self.sprite_compress(sprite_data)
        # Try tile compression, and see if it results in a smaller file size
        tile_data = self.sprite_encode_tile(size_x, size_y, sprite_data, info_byte, bpp)
        if tile_data is not None:
            tile_compressed_data = self.sprite_compress(tile_data)
            # Tile compression adds another 4 bytes for the uncompressed chunked data in the header
            if len(tile_compressed_data) + 4 < len(compressed_data):
                info_byte |= INFO_TILE
                data_len = len(tile_data)
                compressed_data = array.array('B')
                compressed_data.append(data_len & 0xFF)
                compressed_data.append((data_len >> 8) & 0xFF)
                compressed_data.append((data_len >> 16) & 0xFF)
                compressed_data.append((data_len >> 24) & 0xFF)
                compressed_data.extend(tile_compressed_data)

        return (size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, warning)

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

    def fakecompress(self, data):
        i = 0
        output = array.array('B')
        length = len(data)
        while i < length:
            n = min(length - i, 127)
            output.append(n)
            output.extend(data[i:i+n])
            i += n
        return output

    def sprite_compress(self, data):
        if self.compress_grf:
            lz = lz77.LZ77(data)
            stream = lz.encode()
        else:
            stream = self.fakecompress(data)
        return stream

    def sprite_encode_tile(self, size_x, size_y, data, info, bpp, long_format = False):
        long_chunk = size_x > 256

        # There are basically four different encoding configurations here,
        # but just two variables. If the width of the sprite is more than
        # 256, then the chunk could be 'out of bounds' and thus the long
        # chunk format is used. If the sprite is more than 65536 bytes,
        # then the offsets might not fit and the long format method is
        # used. The latter is enabled via recursion if it's needed.
        if not has_transparency(info):
            return None
        trans_offset = transparency_offset(info)
        max_chunk_len = 0x7fff if long_chunk else 0x7f
        line_offset_size = 4 if long_format else 2 # Whether to use 2 or 4 bytes in the list of line offsets
        output = array.array('B', [0] * (line_offset_size * size_y))

        for y in range(size_y):
            # Write offset in the correct place, in little-endian format
            offset = len(output)
            output[y*line_offset_size] = offset & 0xFF
            output[y*line_offset_size + 1] = (offset >> 8) & 0xFF
            if long_format:
                output[y*line_offset_size + 2] = (offset >> 16) & 0xFF
                output[y*line_offset_size + 3] = (offset >> 24) & 0xFF

            line_start = y*size_x*bpp

            line_parts = []
            x1 = 0
            while True:
                # Skip transparent pixels
                while x1 < size_x and data[line_start + x1*bpp + trans_offset] == 0:
                    x1 += 1
                if x1 == size_x:
                    # End-of-line reached
                    break

                # Grab as many non-transparent pixels as possible, but not without x2-x1 going out of bounds
                # Only stop the chunk when encountering 3 consecutive transparent pixels
                x2 = x1 + 1
                while x2 - x1 < max_chunk_len and (
                         (x2 < size_x and data[line_start + x2*bpp + trans_offset] != 0) or
                         (x2 + 1 < size_x and data[line_start + (x2+1)*bpp + trans_offset] != 0) or
                         (x2 + 2 < size_x and data[line_start + (x2+2)*bpp + trans_offset] != 0)):
                    x2 += 1
                line_parts.append((x1, x2))
                x1 = x2

            if len(line_parts) == 0:
                # Completely transparent line
                if long_chunk:
                    output.extend((0, 0x80, 0, 0))
                else:
                    output.extend((0x80, 0))
                continue

            for idx, part in enumerate(line_parts):
                x1, x2 = part
                last_mask = 0x80 if idx == len(line_parts) - 1 else 0
                chunk_len = x2 - x1
                if long_chunk:
                    output.extend((chunk_len & 0xFF,
                                       (chunk_len >> 8) | last_mask,
                                       x1 & 0xFF,
                                       x1 >> 8))
                else:
                    output.extend((chunk_len | last_mask, x1))
                output.extend(data[line_start + x1*bpp : line_start + x2*bpp])

        if len(output) > 65535 and not long_format:
            # Recurse into the long format if that's possible.
            return self.sprite_encode_tile(size_x, size_y, data, info, bpp, True)
        return output

    def recompute_offsets(self, size_x, size_y, xoffset, yoffset, crop_rect):
        # Recompute sizes and offsets after cropping a sprite
        left, right, top, bottom = crop_rect
        size_x -= left + right
        size_y -= top + bottom
        xoffset += left
        yoffset += top
        return size_x, size_y, xoffset, yoffset

    def crop_sprite(self, data, size_x, size_y, info, bpp):
        left, right, top, bottom = 0, 0, 0, 0
        if not has_transparency(info):
            return (data, (left, right, top, bottom))

        trans_offset =  transparency_offset(info)
        line_size = size_x * bpp # size (no. of bytes) of a scan line
        data_size = len(data)

        #Crop the top of the sprite
        while size_y > 1 and not any(data[line_size * top + trans_offset : line_size * (top+1) : bpp]):
            top += 1
            size_y -= 1

        #Crop the bottom of the sprite
        while size_y > 1 and not any(data[data_size - line_size * (bottom+1) + trans_offset : data_size - line_size * bottom : bpp]):
            # Don't use negative indexing, it breaks for the last line (where you'd need index 0)
            bottom += 1
            size_y -= 1

        #Modify data by removing top/bottom
        data = data[line_size * top : data_size - line_size * bottom]

        #Crop the left of the sprite
        while size_x > 1 and not any(data[left * bpp + trans_offset : : line_size]):
            left += 1
            size_x -= 1

        #Crop the right of the sprite
        while size_x > 1 and not any(data[line_size - (right+1) * bpp + trans_offset : : line_size]):
            right += 1
            size_x -= 1

        #Removing left/right data is not easily done by slicing
        #Best to create a new array
        if left + right > 0:
            new_data = array.array('B')
            for y in range(0, size_y):
                a = data[y*line_size + left*bpp : (y+1)*line_size - right*bpp]
                new_data.extend(a)
            data = new_data

        return (data, (left, right, top, bottom))

    def palconvert(self, sprite_str, orig_pal):
        if orig_pal == "LEGACY" and self.palette == "DEFAULT":
            return sprite_str.translate(translate_w2d)
        else:
            return sprite_str

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)

        self.start_sprite(0, 0xfd)
        self.sprite_output.start_sprite(8 + 3 + len(name) + 1 + size)

        self.sprite_output.print_dword(self.sprite_num)
        self.sprite_output.print_dword(3 + len(name) + 1 + size)
        self.sprite_output.print_byte(0xff)
        self.sprite_output.print_byte(0xff)
        self.sprite_output.print_byte(len(name))
        self.print_string(name, force_ascii = True, final_zero = True, stream = self.sprite_output)  # ASCII filenames seems sufficient.
        fp = open(generic.find_file(filename), 'rb')
        while True:
            data = fp.read(1024)
            if len(data) == 0: break
            for d in data:
                self.sprite_output.print_byte(d)
        fp.close()

        self.sprite_output.end_sprite();
        self.end_sprite()

    def end_sprite(self):
        output_base.BinaryOutputBase.end_sprite(self)
        self.sprite_num += 1

