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

import os, hashlib, itertools, json
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

def is_transparent(p, info):
    if (info & INFO_PAL) != 0:
        if (info & INFO_ALPHA) != 0:
            return p[-2] == 0
        return p[-1] == 0
    if (info & INFO_ALPHA) != 0:
        return p[-1] == 0
    return False

class OutputGRF(output_base.BinaryOutputBase):
    def __init__(self, filename, compress_grf, crop_sprites, enable_cache):
        output_base.BinaryOutputBase.__init__(self, filename)
        self.cache_filename = self.filename + ".cache"
        self.cache_index_filename = self.filename + ".cacheindex"
        self.cache_time = 0
        self.compress_grf = compress_grf
        self.crop_sprites = crop_sprites
        self.enable_cache = enable_cache
        self.data_output = []
        self.sprite_output = []
        self.cache_output = []
        self.cached_sprites = {}
        self.md5 = hashlib.md5()
        # sprite_num is deliberately off-by-one because it is used as an
        # id between data and sprite section. For the sprite section an id
        # of 0 is invalid (means end of sprites), and for a non-NewGRF GRF
        # the first sprite is a real sprite.
        self.sprite_num = 1
        # Mapping of filenames to cached image files
        self.cached_image_files = {}
        # used_sprite_files (set from main.py) is used to keep track of what files are used and how often
        self.read_cache()

    def open_file(self):
        return open(self.filename, 'wb')

    def get_md5(self):
        return self.md5.hexdigest()

    def read_cache(self):
        """
        Read the *.grf.cache[index] files, which cache real sprites for faster compilation

        Cache file format description:
        Format of cache index is JSON (JavaScript Object Notation), which is
        easily readable by both humans (for debugging) and machines. Format is as follows:

        A list of dictionaries, each corresponding to a sprite, with the following keys
         - rgb_file: filename of the 32bpp sprite (string)
         - rgb_rect: (uncropped) rectangle of the 32bpp sprite (list with 4 elements (x,y,w,h))
         - mask_file, mask_rect: same as above, but for 8bpp sprite
         - crop: List of 4 positive integers, indicating how much to crop if cropping is enabled 
              Order is (left, right, top, bottom), it is not present if cropping is disabled
         - info: Info byte of the sprite
         - offset: Offset into the cache file for this sprite
         - size: Length of this sprite in the cache file

        Either rgb_file/rect, mask_file/rect, or both must be specified, depending on the sprite
        The cache should contain the sprite data, but not the header (sizes/offsets and such)

        For easy lookup, this information is stored in a dictionary
        Tuples are used because these are hashable

        The key is a (rgb_file, rgb_rect, mask_file, mask_rect, do_crop)-tuple
        The rectangles are 4-tuples, non-existent items (e.g. no rgb) are None
        do_crop is a boolean indicating if this sprite has been cropped

        The value that this key maps to is a 5-tuple, containing:
         - the sprite data (as a string)
         - The 'info' byte of the sprite
         - The cropping information (see above) (None if 'do_crop' in the key is false)
         - Whether the sprite exists in the old (loaded)cache
         - whether the sprite is used by the current GRF

        The cache file itself is simply the binary sprite data with no
        meta-information or padding. Offsets and sizes for the various sprites
        are in the cacheindex file.
        """
        if not self.enable_cache: return
        if not (os.access(self.cache_filename, os.R_OK) and os.access(self.cache_index_filename, os.R_OK)):
            # Cache files don't exist
            return

        index_file = open(self.cache_index_filename, 'r')
        cache_file = open(self.cache_filename, 'rb')
        cache_data = cache_file.read()
        cache_size = len(cache_data)
        self.cache_time = os.path.getmtime(self.cache_filename)

        try:
            # Just assert and print a generic message on errors, as the cache data should be correct
            # Not asserting coould lead to errors later on
            # Also, it doesn't make sense to inform the user about things he shouldn't know about and can't fix
            sprite_index = json.load(index_file)
            assert isinstance(sprite_index, list)
            for sprite in sprite_index:
                assert isinstance(sprite, dict)
                # load RGB (32bpp) data
                rgb_key = (None, None)
                if 'rgb_file' in sprite and 'rgb_rect' in sprite:
                    assert isinstance(sprite['rgb_file'], basestring)
                    assert isinstance(sprite['rgb_rect'], list) and len(sprite['rgb_rect']) == 4
                    assert all(isinstance(num, int) for num in sprite['rgb_rect'])
                    rgb_key = (sprite['rgb_file'], tuple(sprite['rgb_rect']))

                # load Mask (8bpp) data
                mask_key = (None, None)
                if 'mask_file' in sprite and 'mask_rect' in sprite:
                    assert isinstance(sprite['mask_file'], basestring)
                    assert isinstance(sprite['mask_rect'], list) and len(sprite['mask_rect']) == 4
                    assert all(isinstance(num, int) for num in sprite['mask_rect'])
                    mask_key = (sprite['mask_file'], tuple(sprite['mask_rect']))

                # Compose key
                assert any(i is not None for i in rgb_key + mask_key)
                key = rgb_key + mask_key + ('crop' in sprite ,)
                assert key not in self.cached_sprites

                # Read size/offset from cache
                assert 'offset' in sprite and 'size' in sprite
                offset, size = sprite['offset'], sprite['size']
                assert isinstance(offset, int) and isinstance(size, int)
                assert offset >= 0 and size > 0
                assert offset + size <= cache_size
                data = cache_data[offset:offset+size]

                # Read info / cropping data from cache
                assert 'info' in sprite and isinstance(sprite['info'], int)
                info = sprite['info']
                if 'crop' in sprite:
                    assert isinstance(sprite['crop'], list) and len(sprite['crop']) == 4
                    assert all(isinstance(num, int) for num in sprite['crop'])
                    crop = tuple(sprite['crop'])
                else:
                    crop = None

                # Compose value
                value = (data, info, crop, True, False)

                self.cached_sprites[key] = value
        except:
            generic.print_warning(self.cache_index_filename + " contains invalid data, ignoring. Please remove the file and file a bug report if this warning keeps appearing")
            self.cached_sprites = {} # Clear cache

        index_file.close()
        cache_file.close()

    def write_cache(self):
        """
        Write the cache data to the .cache[index] files.
        Refer to L{read_cache} for a format description.
        """
        if not self.enable_cache: return
        index_data = []
        sprite_data = []
        offset = 0

        old_cache_valid = True
        for key, value in self.cached_sprites.iteritems():
            # Unpack key/value
            rgb_file, rgb_rect, mask_file, mask_rect, do_crop = key
            data, info, crop_rect, in_old_cache, in_use = value
            assert do_crop == (crop_rect is not None)

            # If this cache information is exactly the same as the old cache, then we don't bother writing later on
            if not in_use:
                old_cache_valid = False
                continue
            if not in_old_cache:
                old_cache_valid = False

            # Create dictionary with information
            sprite = {}
            if rgb_file is not None:
                sprite['rgb_file'] = rgb_file
                sprite['rgb_rect'] = tuple(rgb_rect)
            if mask_file is not None:
                sprite['mask_file'] = mask_file
                sprite['mask_rect'] = tuple(mask_rect)

            size = len(data)
            sprite['offset'] = offset
            sprite['size'] = size
            sprite['info'] = info
            if do_crop: sprite['crop'] = tuple(crop_rect)

            index_data.append(sprite)
            sprite_data.append(data)
            offset += size

        if old_cache_valid: return

        index_output = json.JSONEncoder(sort_keys = True).encode(index_data)
        cache_output = ''.join(sprite_data)

        index_file = open(self.cache_index_filename, 'w')
        index_file.write(index_output)
        index_file.close()
        cache_file = open(self.cache_filename, 'w')
        cache_file.write(cache_output)
        cache_file.close()

    def update_cache(self, key, info, crop):
        """
        Add a sprite to the sprite cache, possibly overwriting an existing one

        @param key: Cache key of the sprite
        @type key: C{tuple}, see L{read_cache} for more info

        @param info: Info byte of the sprite
        @type info: C{int}

        @param crop: How much was cropped from each side of the sprite
        @type crop: C{tuple}, or C{None} if N/A
        """
        if not self.enable_cache: return
        data = ''.join(self.cache_output)
        self.cache_output = []
        self.cached_sprites[key] = (data, info, crop, False, True)

    def open_image_file(self, filename):
        """
        Obtain a handle to an image file

        @param filename: Name of the file
        @type filename: C{unicode}

        @return: Image file
        @rtype: L{Image}
        """
        assert filename in self.used_sprite_files
        if filename in self.cached_image_files:
            im = self.cached_image_files[filename]
        else:
            im = Image.open(filename)
            self.cached_image_files[filename] = im
        self.mark_image_file_used(filename)
        return im

    def mark_image_file_used(self, filename):
        """
        Indicate that an image file is being used, so the internal book-keeping can be updated

        @param filename: Name of the file
        @type filename: C{unicode}
        """
        assert filename in self.used_sprite_files
        self.used_sprite_files[filename] -= 1
        if self.used_sprite_files[filename] == 0 and filename in self.cached_image_files:
            # Delete from dictionary if it exists, then data will be freed when it goes out of scope
            del self.cached_image_files[filename]

    def pre_close(self):
        output_base.BinaryOutputBase.pre_close(self)

        # Verify that image file counts were correct
        assert not self.cached_image_files, "Invalid sprite file cache"
        # all values should be 0 at this point
        assert not any(self.used_sprite_files.values()), "Invalid sprite file cache"

        #add end-of-chunks
        self._in_sprite = True
        self.print_dword(0, self.data_output)
        self.print_dword(0, self.sprite_output)
        self._in_sprite = False

        #add header
        header = ['\x00', '\x00', 'G', 'R', 'F', '\x82', '\x0D', '\x0A', '\x1A', '\x0A']
        size = len(self.data_output) + 1
        header.append(chr(size & 0xFF))
        header.append(chr((size >> 8) & 0xFF))
        header.append(chr((size >> 16) & 0xFF))
        header.append(chr(size >> 24))
        header.append('\x00') #no compression
        
        for c in header:
            self.file.write(c)
            self.md5.update(c)

        #add data section, and then the sprite section
        for c in self.data_output:
            self.file.write(c)
            self.md5.update(c)
        for c in self.sprite_output:
            self.file.write(c)

    def close(self):
        output_base.BinaryOutputBase.close(self)
        self.write_cache()

    def print_data(self, data, stream):
        """
        Print a chunck of data in one go

        @param data: Data to output
        @type data: C{str}

        @param stream: Stream to output the data to
        @type stream: C{list}
        """
        if stream is None: stream = self.data_output
        stream.append(data)
        self._byte_count += len(data)

    def wb(self, byte, stream):
        if stream is None: stream = self.data_output
        stream.append(chr(byte))

    def print_byte(self, value, stream = None):
        value = self.prepare_byte(value)
        self.wb(value, stream)

    def print_bytex(self, value, pretty_print = None, stream = None):
        self.print_byte(value, stream)

    def print_word(self, value, stream = None):
        value = self.prepare_word(value)
        self.wb(value & 0xFF, stream)
        self.wb(value >> 8, stream)

    def print_wordx(self, value, stream = None):
        self.print_word(value, stream)

    def print_dword(self, value, stream = None):
        value = self.prepare_dword(value)
        self.wb(value & 0xFF, stream)
        self.wb((value >> 8) & 0xFF, stream)
        self.wb((value >> 16) & 0xFF, stream)
        self.wb(value >> 24, stream)

    def print_dwordx(self, value, stream = None):
        self.print_dword(value, stream)

    def _print_utf8(self, char, stream = None):
        for c in unichr(char).encode('utf8'):
            self.print_byte(ord(c), stream)

    def print_string(self, value, final_zero = True, force_ascii = False, stream = None):
        if not grfstrings.is_ascii_string(value):
            if force_ascii:
                raise generic.ScriptError("Expected ascii string but got a unicode string")
            self.print_byte(0xC3, stream)
            self.print_byte(0x9E, stream)
        i = 0
        while i < len(value):
            if value[i] == '\\':
                if value[i+1] in ('\\', '"'):
                    self.print_byte(ord(value[i+1]), stream)
                    i += 2
                elif value[i+1] == 'U':
                    self._print_utf8(int(value[i+2:i+6], 16), stream)
                    i += 6
                else:
                    self.print_byte(int(value[i+1:i+3], 16), stream)
                    i += 3
            else:
                self._print_utf8(ord(value[i]), stream)
                i += 1
        if final_zero: self.print_byte(0, stream)

    def newline(self, msg = "", prefix = "\t"):
        pass

    def comment(self, msg):
        pass

    def start_sprite(self, size, type = 0xFF, data = True):
        if type == 0xFF:
            output_base.BinaryOutputBase.start_sprite(self, size + 5)
            stream = self.data_output if data else self.sprite_output
            if not data:
                # The compression byte (=type) is counted when in the sprite section,
                # however since this is a sound we need to emit the sprite number as well.
                self.print_dword(self.sprite_num, stream)
                self._byte_count -= 3
            self.print_dword(size, stream)
            self.print_byte(type, stream)
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
        assert sprite_info.file is not None or sprite_info.mask_file is not None
        filename_8bpp = None
        filename_32bpp = None
        if sprite_info.bit_depth == 8:
            filename_8bpp = sprite_info.file
        else:
            filename_32bpp = sprite_info.file
            filename_8bpp = sprite_info.mask_file

        im, mask_im = None, None
        im_mask_pal = None
        info_byte = sprite_info.compression.value

        # Select region of image bounded by x/ypos and x/ysize
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        if sprite_info.bit_depth == 8 or sprite_info.mask_pos is None:
            mask_x, mask_y = x, y
        else:
            mask_x = sprite_info.mask_pos[0].value
            mask_y = sprite_info.mask_pos[1].value

        # Check if files exist and if cache is usable
        use_cache = True
        if filename_32bpp is not None:
            if not os.path.exists(filename_32bpp.value):
                raise generic.ImageError("File doesn't exist", filename_32bpp.value)
            if os.path.getmtime(filename_32bpp.value) > self.cache_time:
                use_cache = False

        if filename_8bpp is not None:
            if not os.path.exists(filename_8bpp.value):
                raise generic.ImageError("File doesn't exist", filename_8bpp.value)
            if os.path.getmtime(filename_8bpp.value) > self.cache_time:
                use_cache = False

        # Try finding the file in the cache
        rgb_file, rgb_rect = (filename_32bpp.value, (x, y, size_x, size_y)) if filename_32bpp is not None else (None, None)
        mask_file, mask_rect = (filename_8bpp.value, (mask_x, mask_y, size_x, size_y)) if filename_8bpp is not None else (None, None)
        do_crop = self.crop_sprites and (info_byte & INFO_NOCROP == 0)
        cache_key = (rgb_file, rgb_rect, mask_file, mask_rect, do_crop)
        if cache_key in self.cached_sprites:
            # Use cache either if files are older, of if cache entry was not present
            # in the loaded cache, and thus written by the current grf (occurs if sprites are duplicated)
            if use_cache or not self.cached_sprites[cache_key][3]:
                if filename_8bpp is not None: self.mark_image_file_used(filename_8bpp.value)
                if filename_32bpp is not None:  self.mark_image_file_used(filename_32bpp.value)
                self.wsprite_cache(cache_key, size_x, size_y, sprite_info.xrel.value, sprite_info.yrel.value, sprite_info.zoom_level)
                return

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
                raise generic.ScriptError("Read beyond bounds of image file '%s'" % filename_32bpp.value, filename_32bpp.pos)
            sprite = im.crop((x, y, x + size_x, y + size_y))

        if filename_8bpp is not None:
            mask_im = self.open_image_file(filename_8bpp.value)
            if mask_im.mode != "P":
                raise generic.ImageError("8bpp image does not have a palette", filename_8bpp.value)
            im_mask_pal = palette.validate_palette(mask_im, filename_8bpp.value)
            info_byte |= INFO_PAL

            (im_width, im_height) = mask_im.size
            if mask_x < 0 or mask_y < 0 or mask_x + size_x > im_width or mask_y + size_y > im_height:
                raise generic.ScriptError("Read beyond bounds of image file '%s'" % filename_8bpp.value, filename_8bpp.pos)
            mask_sprite = mask_im.crop((mask_x, mask_y, mask_x + size_x, mask_y + size_y))

            # Check for white pixels; those that cause "artefacts" when shading
            if 255 in mask_sprite.getdata():
                white_pixels = len(filter(lambda p: p == 255, mask_sprite.getdata()))
                pixels = size_x * size_y
                image_pos = generic.PixelPosition(filename_8bpp.value, x, y)
                generic.print_warning("%s: %i of %i pixels (%i%%) are pure white" % (str(image_pos), white_pixels, pixels, white_pixels * 100 / pixels), filename_8bpp.pos)

            mask_sprite_data = self.palconvert(mask_sprite.getdata(), im_mask_pal)

        # Compose pixel information (each pixel is a tuple)
        if (info_byte & INFO_ALPHA) != 0 and (info_byte & INFO_PAL) != 0:
            sprite_data = [(x[0][0], x[0][1], x[0][2], x[0][3], x[1]) for x in zip(sprite.getdata(), mask_sprite_data)]
        elif (info_byte & INFO_RGB) != 0 and (info_byte & INFO_PAL) != 0:
            sprite_data = [(x[0][0], x[0][1], x[0][2], x[1]) for x in zip(sprite.getdata(), mask_sprite_data)]
        elif (info_byte & INFO_RGB) != 0:
            sprite_data = [tuple(x) for x in sprite.getdata()]
        else:
            sprite_data = [(x,) for x in mask_sprite_data]
        self.wsprite(sprite_data, size_x, size_y, sprite_info.xrel.value, sprite_info.yrel.value, info_byte, sprite_info.zoom_level, cache_key)

    def print_empty_realsprite(self):
        self.start_sprite(1)
        self.print_byte(0)
        self.end_sprite()

    def wsprite_header(self, size_x, size_y, size, xoffset, yoffset, info, zoom_level, write_cache):
        self._expected_count += size + 18
        if write_cache: self._expected_count += size # With caching, the image data is written twice
        self.print_dword(self.sprite_num, self.sprite_output)
        self.print_dword(size + 10, self.sprite_output)
        self.print_byte(info, self.sprite_output)
        self.print_byte(zoom_level, self.sprite_output)
        self.print_word(size_y, self.sprite_output)
        self.print_word(size_x, self.sprite_output)
        self.print_word(xoffset, self.sprite_output)
        self.print_word(yoffset, self.sprite_output)

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
        # Returns a compressed data stream and the UNcompressed length
        data_str = ''.join(map(chr, itertools.chain.from_iterable(data)))
        if self.compress_grf:
            lz = lz77.LZ77(data_str)
            stream = lz.encode()
        else:
            stream = self.fakecompress(data_str)
        return stream, len(data_str)

    def wsprite_encoderegular(self, size_x, size_y, data, data_len, xoffset, yoffset, info, zoom_level):
        # Data is already encoded as a string at this point
        chunked = info & INFO_TILE != 0
        size = len(data)
        if chunked:
            size += 4
        self.wsprite_header(size_x, size_y, size, xoffset, yoffset, info, zoom_level, self.enable_cache)
        if chunked:
            self.print_dword(data_len, self.sprite_output)
            if self.enable_cache: self.print_dword(data_len, self.cache_output)
        self.print_data(data, self.sprite_output)
        if self.enable_cache: self.print_data(data, self.cache_output)

    def wsprite_cache(self, cache_key, size_x, size_y, xoffset, yoffset, zoom_level):
        # Write a sprite from the cached data
        data, info, crop_rect, in_old_cache, in_use = self.cached_sprites[cache_key]
        if not in_use:
            self.cached_sprites[cache_key] = (data, info, crop_rect, in_old_cache, True)

        if cache_key[-1]: size_x, size_y, xoffset, yoffset = self.recompute_offsets(size_x, size_y, xoffset, yoffset, crop_rect)
        self.wsprite_header(size_x, size_y, len(data), xoffset, yoffset, info, zoom_level, False)
        self.print_data(data, self.sprite_output)

    def sprite_encode_tile(self, size_x, size_y, data, info, long_format = False):
        long_chunk = size_x > 256

        # There are basically four different encoding configurations here,
        # but just two variables. If the width of the sprite is more than
        # 256, then the chunk could be 'out of bounds' and thus the long
        # chunk format is used. If the sprite is more than 65536 bytes,
        # then the offsets might not fit and the long format method is
        # used. The latter is enabled via recursion if it's needed.
        max_chunk_len = 0x7fff if long_chunk else 0x7f
        data_output = []
        offsets = size_y * [0]
        total_length = (4 if long_format else 2) * size_y
        bpp = len(data[0])

        for y in range(size_y):
            offsets[y] = total_length
            row_data = data[y*size_x : (y+1)*size_x]
            assert size_x == len(row_data)

            line_parts = []
            x1 = 0
            while True:
                # Skip transparent pixels
                while x1 < size_x and is_transparent(row_data[x1], info):
                    x1 += 1
                if x1 == size_x:
                    # End-of-line reached
                    break

                # Grab as many non-transparent pixels as possible, but not without x2-x1 going out of bounds
                x2 = x1 + 1
                while x2 - x1 < max_chunk_len and (
                        (x2 < size_x and not is_transparent(row_data[x2], info)) or
                        (x2 + 1 < size_x and not is_transparent(row_data[x2 + 1], info)) or
                        (x2 + 2 < size_x and not is_transparent(row_data[x2 + 2], info))):
                    x2 += 1
                line_parts.append((x1, x2))
                x1 = x2

            if len(line_parts) == 0:
                # Completely transparant line
                if long_chunk:
                    data_output.append((0, 0x80, 0, 0))
                    total_length += 4
                else:
                    data_output.append((0x80, 0))
                    total_length += 2
                continue

            for idx, part in enumerate(line_parts):
                x1, x2 = part
                last_mask = 0x80 if idx == len(line_parts) - 1 else 0
                chunk_len = x2 - x1
                if long_chunk:
                    data_output.append((chunk_len & 0xFF,
                                       (chunk_len >> 8) | last_mask,
                                       x1 & 0xFF,
                                       x1 >> 8))
                    total_length += 4
                else:
                    data_output.append((chunk_len | last_mask, x1))
                    total_length += 2
                data_output.extend(row_data[x1 : x2])
                total_length += bpp * (x2 - x1)
 
        output = []
        for offset in offsets:
            output.append([offset & 0xFF, (offset >> 8) & 0xFF])
            if long_format:
                output.append([(offset >> 16) & 0xFF, (offset >> 24) & 0xFF])
        output += data_output
        if total_length > 65535 and not long_format:
            # Recurse into the long format if that's possible.
            return self.sprite_encode_tile(size_x, size_y, data, info, True)
        return output

    def recompute_offsets(self, size_x, size_y, xoffset, yoffset, crop_rect):
        # Recompute sizes and offsets after cropping a sprite
        left, right, top, bottom = crop_rect
        size_x -= left + right
        size_y -= top + bottom
        xoffset += left
        yoffset += top
        return size_x, size_y, xoffset, yoffset

    def crop_sprite(self, data, size_x, size_y, xoffset, yoffset, info):
        left, right, top, bottom = 0, 0, 0, 0
        #Crop the top of the sprite
        while size_y > 1 and all(is_transparent(p, info) for p in data[0 : size_x]):
            data = data[size_x:]
            top += 1
            size_y -= 1

        #Crop the bottom of the sprite
        while size_y > 1 and all(is_transparent(p, info) for p in data[-size_x:]):
            data = data[:-size_x]
            bottom += 1
            size_y -= 1

        #Crop the left of the sprite
        while size_x > 1 and all(is_transparent(p, info) for p in data[::size_x]):
            del data[::size_x]
            left += 1
            size_x -= 1

        #Crop the right of the sprite
        while size_x > 1 and all(is_transparent(p, info) for p in data[size_x-1::size_x]):
            del data[size_x-1::size_x]
            right += 1
            size_x -= 1

        return (data, (left, right, top, bottom))

    def palconvert(self, sprite_data, orig_pal):
        if orig_pal == "WIN" and self.palette == "DOS":
            return (palmap_w2d[p] for p in sprite_data)
        return sprite_data

    def wsprite(self, sprite_data, size_x, size_y, xoffset, yoffset, info, zoom_level, cache_key):
        assert len(sprite_data) == size_x * size_y
        if self.crop_sprites and (info & INFO_NOCROP == 0):
            sprite_data, crop_rect = self.crop_sprite(sprite_data, size_x, size_y, xoffset, yoffset, info)
            size_x, size_y, xoffset, yoffset = self.recompute_offsets(size_x, size_y, xoffset, yoffset, crop_rect)
        else:
            crop_rect = None
        assert len(sprite_data) == size_x * size_y

        compressed_data, data_len = self.sprite_compress(sprite_data)
        # Try tile compression, and see if it results in a smaller file size
        tile_data = self.sprite_encode_tile(size_x, size_y, sprite_data, info)
        if tile_data is not None:
            tile_compressed_data, tile_data_len = self.sprite_compress(tile_data)
            # Tile compression adds another 4 bytes for the uncompressed chunked data in the header
            if len(tile_compressed_data) + 4 < len(compressed_data):
                info |= INFO_TILE
                compressed_data, data_len = tile_compressed_data, tile_data_len
        self.wsprite_encoderegular(size_x, size_y, compressed_data, data_len, xoffset, yoffset, info, zoom_level)
        self.update_cache(cache_key, info, crop_rect)

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)
        total = 3 + len(name) + 1 + size

        self.start_sprite(total, 0xff, False)
        self.print_byte(0xff, self.sprite_output)
        self.print_byte(len(name), self.sprite_output)
        self.print_string(name, force_ascii = True, final_zero = True, stream = self.sprite_output)  # ASCII filenames seems sufficient.
        fp = open(filename, 'rb')
        while True:
            data = fp.read(1024)
            if len(data) == 0: break
            for d in data:
                self.print_byte(ord(d), self.sprite_output)
        fp.close()

        self.print_dword(4)
        self.print_byte(0xfd)
        self.print_dword(self.sprite_num)
        self._byte_count -= 9
        self.end_sprite()

    def end_sprite(self):
        output_base.BinaryOutputBase.end_sprite(self)
        self.sprite_num += 1

