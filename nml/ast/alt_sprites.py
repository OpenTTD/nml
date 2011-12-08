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

from nml import expression, generic, global_constants
from nml.actions import real_sprite
from nml.ast import base_statement
import os, Image

"""
List with all AltSpritesBlocks encountered in the nml file.
"""
alt_sprites_list = []

class AltSpritesBlock(base_statement.BaseStatement):
    """
    AST Node for alternative graphics. These are normally 32bpp graphics, possible
    for a higher zoom-level than the default sprites.

    @ivar name: The name of the replace/font_glyph/replace_new/spriteblock-block this
                block contains alternative graphics for.
    @type name: L{expression.Identifier}

    @ivar zoom_level: The zoomlevel these graphics are for.
    @type zoom_level: L{expression.Expression}

    @ivar pcx: Default graphics file for the sprites in this block.
    @type pcx: L{expression.StringLiteral} or C{None}

    @ivar sprite_list: List of real sprites or templates expanding to real sprites.
    @type sprite_list: Heterogeneous C{list} of L{RealSprite}, L{TemplateUsage}
    """
    def __init__(self, param_list, sprite_list, pos):
        base_statement.BaseStatement.__init__(self, "alt_sprites-block", pos)
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("alternative_sprites-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        self.zoom_level = param_list[1]
        self.pcx = param_list[2] if len(param_list) >= 3 else None
        self.sprite_list = sprite_list


    def pre_process(self):
        if self.pcx:
            self.pcx.reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("alternative_sprites-block parameter 3 'file' must be a string literal", self.pcx.pos)
        alt_sprites_list.append(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Alternative sprites'
        print (indentation+2)*' ' + 'Replacement for sprite:', str(self.name)
        print (indentation+2)*' ' + 'Zoom level:', str(self.zoom_level)
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        # Alternative sprites are not part of the final grf/nfo file, they're wirtten
        # as separate png files intsead. As such we don't return any actions. Creating
        # the png files happens in process.
        return []

    def process(self, dir_name, block_names):
        """
        Create seperate png files for every sprite. For OpenTTD to be able
        to read those files they have to be in a directory with the same name
        as the grf and have <sprite_id>.png as name. For the extra-zoom-levels
        branch the png files have to be named <sprite_id>_z<zoom_level>.png.
        The default zoom level is number 2.

        @param dir_name: The name of the directory where to create the png files.
        @type  dir_name: C{str}

        @param block_names: Mapping of block-names to sprite ids.
        @type  block_names: C{dict} of C{str} to C{int}
        """
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        sprite_id = self.name.reduce_constant([block_names]).value
        zoom_level = self.zoom_level.reduce_constant(global_constants.const_list).value
        sprite_list = [action.sprite for action in real_sprite.parse_sprite_list(self.sprite_list, self.pcx)]
        for sprite in sprite_list:
            if sprite.is_empty:
                sprite_id += 1
                continue
            # Both the extra-zoom-levels branch and clean trunk support the filename
            # without _z2 at the end. Higher zoom-levels are not supported by clean
            # trunk anyway, so follow the format needed for extra-zoom-levels there.
            postfix = "" if zoom_level == 2 else "_z" + str(zoom_level)
            filename = os.path.join(dir_name, str(sprite_id) + postfix + ".png")
            mask_filename = os.path.join(dir_name, str(sprite_id) + postfix + "m.png")
            write_32bpp_sprite(sprite, filename, mask_filename)
            sprite_id += 1

def write_32bpp_sprite(sprite_info, filename, mask_filename):
    """
    Actually write a png file with a single sprite.

    @param sprite_info: Information about filename and offsets/size of the sprite in the file.
    @type  sprite_info: L{RealSprite}

    @param filename: Name of the file to create.
    @type  filename: C{str}
    """
    sprite_info.validate_size()
    if not os.path.exists(sprite_info.file.value):
        raise generic.ImageError("File doesn't exist", sprite_info.file.value)
    im = Image.open(sprite_info.file.value)
    if im.mode != "RGBA":
        raise generic.ImageError("Not an RGBA image", sprite_info.file.value)
    x = sprite_info.xpos.value
    y = sprite_info.ypos.value
    size_x = sprite_info.xsize.value
    size_y = sprite_info.ysize.value
    sprite = im.crop((x, y, x + size_x, y + size_y))
    sprite.info["x_offs"] = str(sprite_info.xrel.value)
    sprite.info["y_offs"] = str(sprite_info.yrel.value)
    pngsave(sprite, filename)
    if sprite_info.mask_file:
        im = Image.open(sprite_info.mask_file.value)
        if im.mode != "P":
            raise generic.ImageError("Not a paletted image", sprite_info.file.value)
        sprite = im.crop((x, y, x + size_x, y + size_y))
        pngsave(sprite, mask_filename)

def pngsave(im, file):
    """
    Wrapper around PIL 1.1.6 Image.save to preserve PNG metadata.

    public domain, Nick Galbreath
    http://blog.modp.com/2007/08/python-pil-and-png-metadata-take-2.html
    """
    # these can be automatically added to Image.info dict
    # they are not user-added metadata
    reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')

    # undocumented class
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()

    # copy metadata into new object
    for k, v in im.info.iteritems():
        if k in reserved: continue
        meta.add_text(k, v, 0)

    # and save
    im.save(file, "PNG", pnginfo=meta)


