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

import array, json, os
from nml import generic

class SpriteCache(object):
    """
    Cache for compressed sprites.

    @ivar cache_filename: Filename of cache data file.
    @type cache_filename: C{str}

    @ivar cache_index_filename: Filename of cache index file.
    @type cache_index_filename: C{str}

    @ivar cache_time: Date of cache files. The cache is invalid, if the source image files are newer.
    @type cache_time: C{int}

    @ivar cached_sprites: Cache contents
    @type cached_sprites: C{dict} mapping cache keys to cache items.

    Cache file format description:
        Format of cache index is JSON (JavaScript Object Notation), which is
        easily readable by both humans (for debugging) and machines. Format is as follows:

        A list of dictionaries, each corresponding to a sprite, with the following keys
         - rgb_file: filename of the 32bpp sprite (string)
         - rgb_rect: (uncropped) rectangle of the 32bpp sprite (list with 4 elements (x,y,w,h))
         - mask_file, mask_rect: same as above, but for 8bpp sprite
         - mask_pal: palette of mask file, 'DEFAULT' or 'LEGACY'. Not present if 'mask_file' is not present.
         - crop: List of 4 positive integers, indicating how much to crop if cropping is enabled
              Order is (left, right, top, bottom), it is not present if cropping is disabled
         - info: Info byte of the sprite
         - warning: Warning about white pixels (optional)
         - offset: Offset into the cache file for this sprite
         - size: Length of this sprite in the cache file

        Either rgb_file/rect, mask_file/rect, or both must be specified, depending on the sprite
        The cache should contain the sprite data, but not the header (sizes/offsets and such)

        For easy lookup, this information is stored in a dictionary
        Tuples are used because these are hashable

        The key is a (rgb_file, rgb_rect, mask_file, mask_rect, do_crop, palette)-tuple
        The rectangles are 4-tuples, non-existent items (e.g. no rgb) are None
        do_crop is a boolean indicating if this sprite has been cropped
        palette is a string identifier

        The value that this key maps to is a 6-tuple, containing:
         - the sprite data (as a byte array)
         - The 'info' byte of the sprite
         - The cropping information (see above) (None if 'do_crop' in the key is false)
         - The warning that should be displayed if this sprite is used (None if N/A)
         - Whether the sprite exists in the old (loaded)cache
         - whether the sprite is used by the current GRF

        The cache file itself is simply the binary sprite data with no
        meta-information or padding. Offsets and sizes for the various sprites
        are in the cacheindex file.
    """
    def __init__(self, filename):
        self.cache_filename = filename + ".cache"
        self.cache_index_filename = filename + ".cacheindex"
        self.cache_time = 0
        self.cached_sprites = {}

    def get_item(self, cache_key, palette):
        """
        Get item from cache.

        @param cache_key: Sprite metadata key, as returned by RealSprite.get_cache_key
        @type  cache_key: C{tuple}

        @param palette: Palette identifier, one of palette.palette_name
        @type  palette: C{str}

        @return: Cache item
        @rtype: C{tuple} or C{None}
        """

        if cache_key[2] is not None:
            key = cache_key + (palette, )
        else:
            key = cache_key + (None, )
        return self.cached_sprites.get(key, None)

    def add_item(self, cache_key, palette, item):
        """
        Add item to cache.

        @param cache_key: Sprite metadata key, as returned by RealSprite.get_cache_key
        @type  cache_key: C{tuple}

        @param palette: Palette identifier, one of palette.palette_name
        @type  palette: C{str}

        @param item: Cache item
        @type  item: C{tuple}
        """

        if cache_key[2] is not None:
            key = cache_key + (palette, )
        else:
            key = cache_key + (None, )
        self.cached_sprites[key] = item

    def read_cache(self):
        """
        Read the *.grf.cache[index] files.
        """
        if not (os.access(self.cache_filename, os.R_OK) and os.access(self.cache_index_filename, os.R_OK)):
            # Cache files don't exist
            return

        index_file = open(self.cache_index_filename, 'r')
        cache_file = open(self.cache_filename, 'rb')
        cache_data = array.array('B')
        cache_size = os.fstat(cache_file.fileno()).st_size
        cache_data.fromfile(cache_file, cache_size)
        assert cache_size == len(cache_data)
        self.cache_time = os.path.getmtime(self.cache_filename)

        try:
            # Just assert and print a generic message on errors, as the cache data should be correct
            # Not asserting could lead to errors later on
            # Also, it doesn't make sense to inform the user about things he shouldn't know about and can't fix
            sprite_index = json.load(index_file)
            assert isinstance(sprite_index, list)
            for sprite in sprite_index:
                assert isinstance(sprite, dict)
                # load RGB (32bpp) data
                rgb_key = (None, None)
                if 'rgb_file' in sprite and 'rgb_rect' in sprite:
                    assert isinstance(sprite['rgb_file'], str)
                    assert isinstance(sprite['rgb_rect'], list) and len(sprite['rgb_rect']) == 4
                    assert all(isinstance(num, int) for num in sprite['rgb_rect'])
                    rgb_key = (sprite['rgb_file'], tuple(sprite['rgb_rect']))

                # load Mask (8bpp) data
                mask_key = (None, None)
                if 'mask_file' in sprite and 'mask_rect' in sprite:
                    assert isinstance(sprite['mask_file'], str)
                    assert isinstance(sprite['mask_rect'], list) and len(sprite['mask_rect']) == 4
                    assert all(isinstance(num, int) for num in sprite['mask_rect'])
                    mask_key = (sprite['mask_file'], tuple(sprite['mask_rect']))

                palette_key = None
                if 'mask_pal' in sprite:
                    palette_key = sprite['mask_pal']

                # Compose key
                assert any(i is not None for i in rgb_key + mask_key)
                key = rgb_key + mask_key + ('crop' in sprite, palette_key)
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

                if 'warning' in sprite:
                    assert isinstance(sprite['warning'], str)
                    warning = sprite['warning']
                else:
                    warning = None

                # Compose value
                value = (data, info, crop, warning, True, False)

                # Check if cache item is still valid
                is_valid = True
                if rgb_key[0] is not None:
                    if os.path.getmtime(generic.find_file(rgb_key[0])) > self.cache_time:
                        is_valid = False

                if mask_key[0] is not None:
                    if os.path.getmtime(generic.find_file(mask_key[0])) > self.cache_time:
                        is_valid = False

                # Drop items from older spritecache format without palette entry
                if (mask_key[0] is None) != (palette_key is None):
                    is_valid = False

                if is_valid:
                    self.cached_sprites[key] = value
        except:
            generic.print_warning(self.cache_index_filename + " contains invalid data, ignoring. Please remove the file and file a bug report if this warning keeps appearing")
            self.cached_sprites = {} # Clear cache

        index_file.close()
        cache_file.close()

    def write_cache(self):
        """
        Write the cache data to the .cache[index] files.
        """
        index_data = []
        sprite_data = array.array('B')
        offset = 0

        old_cache_valid = True
        for key, value in list(self.cached_sprites.items()):
            # Unpack key/value
            rgb_file, rgb_rect, mask_file, mask_rect, do_crop, mask_pal = key
            data, info, crop_rect, warning, in_old_cache, in_use = value
            assert do_crop == (crop_rect is not None)
            assert (mask_file is None) == (mask_pal is None)

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
                sprite['mask_pal'] = mask_pal

            size = len(data)
            sprite['offset'] = offset
            sprite['size'] = size
            sprite['info'] = info
            if do_crop: sprite['crop'] = tuple(crop_rect)
            if warning is not None:
                sprite['warning'] = warning

            index_data.append(sprite)
            sprite_data.extend(data)
            offset += size

        if old_cache_valid: return

        index_output = json.JSONEncoder(sort_keys = True).encode(index_data)

        index_file = open(self.cache_index_filename, 'w')
        index_file.write(index_output)
        index_file.close()
        cache_file = open(self.cache_filename, 'wb')
        sprite_data.tofile(cache_file)
        cache_file.close()
