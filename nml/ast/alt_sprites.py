from nml import expression, generic, global_constants
from nml.actions import real_sprite
import os, Image

alt_sprites_list = []

class AltSpritesBlock(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("alternative_sprites-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        self.zoom_level = param_list[1]
        if len(param_list) >= 3:
            self.pcx = param_list[2].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("alternative_sprites-block parameter 3 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos

    def pre_process(self):
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
        return []

    def process(self, dir_name, block_names):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        sprite_id = self.name.reduce_constant([block_names]).value
        zoom_level = self.zoom_level.reduce_constant(global_constants.const_list).value
        sprite_list = [action.sprite for action in real_sprite.parse_sprite_list(self.sprite_list, self.pcx)]
        for sprite in sprite_list:
            if sprite.is_empty:
                sprite_id += 1
                continue
            postfix = "" if zoom_level == 2 else "_z" + str(zoom_level)
            filename = os.path.join(dir_name, str(sprite_id) + postfix + ".png")
            write_32bpp_sprite(sprite, filename)
            sprite_id += 1

def write_32bpp_sprite(sprite_info, filename):
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

#
# wrapper around PIL 1.1.6 Image.save to preserve PNG metadata
#
# public domain, Nick Galbreath
# http://blog.modp.com/2007/08/python-pil-and-png-metadata-take-2.html
#
def pngsave(im, file):
    # these can be automatically added to Image.info dict
    # they are not user-added metadata
    reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')

    # undocumented class
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()

    # copy metadata into new object
    for k,v in im.info.iteritems():
        if k in reserved: continue
        meta.add_text(k, v, 0)

    # and save
    im.save(file, "PNG", pnginfo=meta)


