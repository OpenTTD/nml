import nml.ast
from nml.generic import *

class RealSpriteAction:
    def __init__(self, sprite, pcx, last = False):
        self.sprite = sprite
        self.pcx = pcx
        self.last = last
    
    def prepare_output(self):
        pass
    
    def write(self, file):
        if isinstance(self.sprite, nml.ast.EmptyRealSprite):
            file.print_empty_realsprite()
            if self.last: file.newline()
            return
        file.print_sprite(self.pcx, self.sprite)
        file.newline()
        if self.last: file.newline()
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

real_sprite_compression_flags = {
    'NORMAL'       : 0x00,
    'TILE'         : 0x08,
    'UNCOMPRESSED' : 0x00,
    'COMPRESSED'   : 0x02,
    'CROP'         : 0x00,
    'NOCROP'       : 0x40,
}
