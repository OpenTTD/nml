import ast
from generic import *

class RealSpriteAction:
    def __init__(self, sprite, pcx):
        self.sprite = sprite
        self.pcx = pcx
    
    def write(self, file):
        #<Sprite-number> <filename> <xpos> <ypos> <compression> <ysize> <xsize> <xrel> <yrel>
        file.write("-1 ")
        file.write(self.pcx + " ")
        print_decimal(file, self.sprite.xpos.value)
        print_decimal(file, self.sprite.ypos.value)
        print_bytex(file, self.sprite.compression.value)
        print_decimal(file, self.sprite.ysize.value)
        print_decimal(file, self.sprite.xsize.value)
        print_decimal(file, self.sprite.xrel.value)
        print_decimal(file, self.sprite.yrel.value)
        file.write("\n")
    
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
