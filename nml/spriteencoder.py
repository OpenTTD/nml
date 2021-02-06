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

import array

from nml import generic, lz77, palette, spritecache
from nml.actions import real_sprite

try:
    from PIL import Image
except ImportError:
    # Image is required only when using graphics
    pass

# Some constants for the 'info' byte
INFO_RGB = 1
INFO_ALPHA = 2
INFO_PAL = 4
INFO_TILE = 8
INFO_NOCROP = 0x40


def get_bpp(info):
    bpp = 0
    if (info & INFO_RGB) != 0:
        bpp += 3
    if (info & INFO_ALPHA) != 0:
        bpp += 1
    if (info & INFO_PAL) != 0:
        bpp += 1
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


class SpriteEncoder:
    """
    Algorithms for cropping and compressing sprites. That is encoding source images into GRF sprites.

    @ivar compress_grf: Compress sprites.
    @type compress_grf: C{bool}

    @ivar crop_sprites: Crop sprites if possible.
    @type crop_sprites: C{bool}

    @ivar palette: Palette for encoding, see L{palette.palette_name}.
    @type palette: C{str}

    @ivar cached_image_files: Currently opened source image files.
    @type cached_image_files: C{dict} mapping C{str} to C{Image}
    """

    def __init__(self, compress_grf, crop_sprites, palette):
        self.compress_grf = compress_grf
        self.crop_sprites = crop_sprites
        self.palette = palette
        self.sprite_cache = spritecache.SpriteCache()
        self.cached_image_files = {}

    def open(self, sprite_files):
        """
        Start the encoder, read caches, and stuff.

        @param sprite_files: List of sprites per source image file.
        @type  sprite_files: C{dict} that maps (C{tuple} of C{str}) to (C{RealSprite})
        """
        num_sprites = sum(len(sprite_list) for sprite_list in sprite_files.values())

        generic.print_progress("Encoding ...")

        num_cached = 0
        num_dup = 0
        num_enc = 0
        num_orphaned = 0
        count_sprites = 0
        for sources, sprite_list in sprite_files.items():
            # Iterate over sprites grouped by source image file.
            #  - Open source files only once. (speed)
            #  - Do not keep files around for long. (memory)

            source_name = "_".join(src for src in sources if src is not None)

            local_cache = spritecache.SpriteCache(sources)
            local_cache.read_cache()

            for sprite_info in sprite_list:
                count_sprites += 1
                generic.print_progress(
                    "Encoding {}/{}: {}".format(count_sprites, num_sprites, source_name), incremental=True
                )

                cache_key = sprite_info.get_cache_key(self.crop_sprites)
                cache_item = local_cache.get_item(cache_key, self.palette)

                in_use = False
                in_old_cache = False
                if cache_item is not None:
                    # Write a sprite from the cached data
                    compressed_data, info_byte, crop_rect, pixel_stats, in_old_cache, in_use = cache_item
                    if in_use:
                        num_dup += 1
                    else:
                        num_cached += 1
                else:
                    (
                        size_x,
                        size_y,
                        xoffset,
                        yoffset,
                        compressed_data,
                        info_byte,
                        crop_rect,
                        pixel_stats,
                    ) = self.encode_sprite(sprite_info)
                    num_enc += 1

                # Store sprite in cache, unless already up-to-date
                if not in_use:
                    cache_item = (compressed_data, info_byte, crop_rect, pixel_stats, in_old_cache, True)
                    local_cache.add_item(cache_key, self.palette, cache_item)

            # Delete all files from dictionary to free memory
            self.cached_image_files.clear()

            num_orphaned += local_cache.count_orphaned()

            # Only write cache if compression is enabled. Uncompressed data is not worth to be cached.
            if self.compress_grf:
                local_cache.write_cache()

            # Transfer data to global cache for later usage
            self.sprite_cache.cached_sprites.update(local_cache.cached_sprites)

        generic.print_progress("Encoding ...", incremental=True)
        generic.clear_progress()
        generic.print_info(
            "{} sprites, {} cached, {} orphaned, {} duplicates, {} newly encoded ({})".format(
                num_sprites, num_cached, num_orphaned, num_dup, num_enc, "native" if lz77.is_native else "python"
            )
        )

    def close(self):
        """
        Close the encoder, validate data, write caches, and stuff.
        """
        pass

    def get(self, sprite_info):
        """
        Get encoded sprite date, either from cache, or new.

        @param sprite_info: Sprite meta data
        @type  sprite_info: C{RealSprite}
        """

        # Try finding the file in the cache
        # open() should have put all sprites into it.
        cache_key = sprite_info.get_cache_key(self.crop_sprites)
        cache_item = self.sprite_cache.get_item(cache_key, self.palette)

        assert cache_item is not None

        compressed_data, info_byte, crop_rect, pixel_stats, in_old_cache, in_use = cache_item

        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        xoffset = sprite_info.xrel.value
        yoffset = sprite_info.yrel.value
        if cache_key[-1]:
            size_x, size_y, xoffset, yoffset = self.recompute_offsets(size_x, size_y, xoffset, yoffset, crop_rect)

        warnings = []
        total = pixel_stats.get("total", 0)
        if total > 0:
            if cache_key[0] is not None:
                image_32_pos = generic.PixelPosition(cache_key[0], cache_key[1][0], cache_key[1][1])
                alpha = pixel_stats.get("alpha", 0)
                if alpha > 0 and (sprite_info.flags.value & real_sprite.FLAG_NOALPHA) != 0:
                    warnings.append(
                        "{}: {:d} of {:d} pixels ({:d}%) are semi-transparent, but NOALPHA is in flags".format(
                            str(image_32_pos), alpha, total, alpha * 100 // total
                        )
                    )

            if cache_key[2] is not None:
                image_8_pos = generic.PixelPosition(cache_key[2], cache_key[3][0], cache_key[3][1])
                white = pixel_stats.get("white", 0)
                anim = pixel_stats.get("anim", 0)
                if white > 0 and (sprite_info.flags.value & real_sprite.FLAG_WHITE) == 0:
                    warnings.append(
                        "{}: {:d} of {:d} pixels ({:d}%) are pure white, but WHITE isn't in flags".format(
                            str(image_8_pos), white, total, white * 100 // total
                        )
                    )
                if anim > 0 and (sprite_info.flags.value & real_sprite.FLAG_ANIM) == 0:
                    warnings.append(
                        "{}: {:d} of {:d} pixels ({:d}%) are animated, but ANIM isn't in flags".format(
                            str(image_8_pos), anim, total, anim * 100 // total
                        )
                    )

        return (size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, warnings)

    def open_image_file(self, filename):
        """
        Obtain a handle to an image file

        @param filename: Name of the file
        @type  filename: C{str}

        @return: Image file
        @rtype:  L{Image}
        """
        if filename in self.cached_image_files:
            im = self.cached_image_files[filename]
        else:
            im = Image.open(generic.find_file(filename))
            self.cached_image_files[filename] = im
        return im

    def encode_sprite(self, sprite_info):
        """
        Crop and compress a real sprite.

        @param sprite_info: Sprite meta data
        @type  sprite_info: C{RealSprite}

        @return: size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, pixel_stats
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
        info_byte = INFO_NOCROP if (sprite_info.flags.value & real_sprite.FLAG_NOCROP) != 0 else 0
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        xoffset = sprite_info.xrel.value
        yoffset = sprite_info.yrel.value

        # Select region of image bounded by x/ypos and x/ysize
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        if sprite_info.bit_depth == 8 or sprite_info.mask_pos is None:
            mask_x, mask_y = x, y
        else:
            mask_x = sprite_info.mask_pos[0].value
            mask_y = sprite_info.mask_pos[1].value

        pixel_stats = {"total": size_x * size_y, "alpha": 0, "white": 0, "anim": 0}

        # Read and validate image data
        if filename_32bpp is not None:
            im = self.open_image_file(filename_32bpp.value)
            if im.mode not in ("RGB", "RGBA"):
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ImageError("32bpp image is not a full colour RGB(A) image.", filename_32bpp.value, pos)
            info_byte |= INFO_RGB
            if im.mode == "RGBA":
                info_byte |= INFO_ALPHA

            (im_width, im_height) = im.size
            if x < 0 or y < 0 or x + size_x > im_width or y + size_y > im_height:
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ScriptError("Read beyond bounds of image file '{}'".format(filename_32bpp.value), pos)
            try:
                sprite = im.crop((x, y, x + size_x, y + size_y))
            except OSError:
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ImageError("Failed to crop 32bpp {} image".format(im.format), filename_32bpp.value, pos)
            rgb_sprite_data = sprite.tobytes()

            if (info_byte & INFO_ALPHA) != 0:
                # Check for half-transparent pixels (not valid for ground sprites)
                pixel_stats["alpha"] = sum(0x00 < p < 0xFF for p in rgb_sprite_data[3::4])

        if filename_8bpp is not None:
            mask_im = self.open_image_file(filename_8bpp.value)
            if mask_im.mode != "P":
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ImageError("8bpp image does not have a palette", filename_8bpp.value, pos)
            im_mask_pal = palette.validate_palette(mask_im, filename_8bpp.value)
            info_byte |= INFO_PAL

            (im_width, im_height) = mask_im.size
            if mask_x < 0 or mask_y < 0 or mask_x + size_x > im_width or mask_y + size_y > im_height:
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ScriptError("Read beyond bounds of image file '{}'".format(filename_8bpp.value), pos)
            try:
                mask_sprite = mask_im.crop((mask_x, mask_y, mask_x + size_x, mask_y + size_y))
            except OSError:
                pos = generic.build_position(sprite_info.poslist)
                raise generic.ImageError(
                    "Failed to crop 8bpp {} image".format(mask_im.format), filename_8bpp.value, pos
                )
            mask_sprite_data = self.palconvert(mask_sprite.tobytes(), im_mask_pal)

            # Check for white pixels; those that cause "artefacts" when shading
            pixel_stats["white"] = sum(p == 255 for p in mask_sprite_data)

            # Check for palette animation colours
            if self.palette == "DEFAULT":
                pixel_stats["anim"] = sum(0xE3 <= p <= 0xFE for p in mask_sprite_data)
            else:
                pixel_stats["anim"] = sum(0xD9 <= p <= 0xF4 for p in mask_sprite_data)

        # Compose pixel information in an array of bytes
        sprite_data = array.array("B")
        if (info_byte & INFO_RGB) != 0 and (info_byte & INFO_PAL) != 0:
            mask_data = array.array("B", mask_sprite_data)  # Convert to numeric
            rgb_data = array.array("B", rgb_sprite_data)
            if (info_byte & INFO_ALPHA) != 0:
                for i in range(len(mask_sprite_data)):
                    sprite_data.extend(rgb_data[4 * i : 4 * (i + 1)])
                    sprite_data.append(mask_data[i])
            else:
                for i in range(len(mask_sprite_data)):
                    sprite_data.extend(rgb_data[3 * i : 3 * (i + 1)])
                    sprite_data.append(mask_data[i])
        elif (info_byte & INFO_RGB) != 0:
            sprite_data.frombytes(rgb_sprite_data)
        else:
            sprite_data.frombytes(mask_sprite_data)

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
                compressed_data = array.array("B")
                compressed_data.append(data_len & 0xFF)
                compressed_data.append((data_len >> 8) & 0xFF)
                compressed_data.append((data_len >> 16) & 0xFF)
                compressed_data.append((data_len >> 24) & 0xFF)
                compressed_data.extend(tile_compressed_data)

        return (size_x, size_y, xoffset, yoffset, compressed_data, info_byte, crop_rect, pixel_stats)

    def fakecompress(self, data):
        i = 0
        output = array.array("B")
        length = len(data)
        while i < length:
            n = min(length - i, 127)
            output.append(n)
            output.extend(data[i : i + n])
            i += n
        return output

    def sprite_compress(self, data):
        if self.compress_grf:
            stream = lz77.encode(data)
        else:
            stream = self.fakecompress(data)
        return stream

    def sprite_encode_tile(self, size_x, size_y, data, info, bpp, long_format=False):
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
        max_chunk_len = 0x7FFF if long_chunk else 0x7F
        line_offset_size = 4 if long_format else 2  # Whether to use 2 or 4 bytes in the list of line offsets
        output = array.array("B", [0] * (line_offset_size * size_y))

        for y in range(size_y):
            # Write offset in the correct place, in little-endian format
            offset = len(output)
            output[y * line_offset_size] = offset & 0xFF
            output[y * line_offset_size + 1] = (offset >> 8) & 0xFF
            if long_format:
                output[y * line_offset_size + 2] = (offset >> 16) & 0xFF
                output[y * line_offset_size + 3] = (offset >> 24) & 0xFF

            line_start = y * size_x * bpp

            line_parts = []
            x1 = 0
            while True:
                # Skip transparent pixels
                while x1 < size_x and data[line_start + x1 * bpp + trans_offset] == 0:
                    x1 += 1
                if x1 == size_x:
                    # End-of-line reached
                    break

                # Grab as many non-transparent pixels as possible, but not without x2-x1 going out of bounds
                # Only stop the chunk when encountering 3 consecutive transparent pixels
                x2 = x1 + 1
                while x2 - x1 < max_chunk_len and (
                    (x2 < size_x and data[line_start + x2 * bpp + trans_offset] != 0)
                    or (x2 + 1 < size_x and data[line_start + (x2 + 1) * bpp + trans_offset] != 0)
                    or (x2 + 2 < size_x and data[line_start + (x2 + 2) * bpp + trans_offset] != 0)
                ):
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
                    output.extend((chunk_len & 0xFF, (chunk_len >> 8) | last_mask, x1 & 0xFF, x1 >> 8))
                else:
                    output.extend((chunk_len | last_mask, x1))
                output.extend(data[line_start + x1 * bpp : line_start + x2 * bpp])

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

        trans_offset = transparency_offset(info)
        line_size = size_x * bpp  # size (no. of bytes) of a scan line
        data_size = len(data)

        # Crop the top of the sprite
        while size_y > 1 and not any(data[line_size * top + trans_offset : line_size * (top + 1) : bpp]):
            top += 1
            size_y -= 1

        # Crop the bottom of the sprite
        while size_y > 1 and not any(
            data[data_size - line_size * (bottom + 1) + trans_offset : data_size - line_size * bottom : bpp]
        ):
            # Don't use negative indexing, it breaks for the last line (where you'd need index 0)
            bottom += 1
            size_y -= 1

        # Modify data by removing top/bottom
        data = data[line_size * top : data_size - line_size * bottom]

        # Crop the left of the sprite
        while size_x > 1 and not any(data[left * bpp + trans_offset :: line_size]):
            left += 1
            size_x -= 1

        # Crop the right of the sprite
        while size_x > 1 and not any(data[line_size - (right + 1) * bpp + trans_offset :: line_size]):
            right += 1
            size_x -= 1

        # Removing left/right data is not easily done by slicing
        # Best to create a new array
        if left + right > 0:
            new_data = array.array("B")
            for y in range(0, size_y):
                a = data[y * line_size + left * bpp : (y + 1) * line_size - right * bpp]
                new_data.extend(a)
            data = new_data

        return (data, (left, right, top, bottom))

    def palconvert(self, sprite_str, orig_pal):
        if orig_pal == "LEGACY" and self.palette == "DEFAULT":
            return sprite_str.translate(real_sprite.translate_w2d)
        else:
            return sprite_str
