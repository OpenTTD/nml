import ast
from generic import *

class RealSpriteAction:
    def __init__(self, sprite, pcx, compression = None):
        self.xpos = sprite.xpos
        self.ypos = sprite.ypos
        self.xsize = sprite.xsize
        self.ysize = sprite.ysize
        self.xrel = sprite.xrel
        self.yrel = sprite.yrel
        self.pcx = pcx
        self.compression = compression if compression is not None else sprite.compression
    
    def write(self, file):
        #<Sprite-number> <filename> <xpos> <ypos> <compression> <ysize> <xsize> <xrel> <yrel>
        file.write("-1 ")
        file.write(self.pcx + " ")
        print_decimal(file, self.xpos)
        print_decimal(file, self.ypos)
        print_bytex(file, self.compression)
        print_decimal(file, self.ysize)
        print_decimal(file, self.xsize)
        print_decimal(file, self.xrel)
        print_decimal(file, self.yrel)
        file.write("\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

compression_flags = {
    'NORMAL' : 0x01,
    'STORE_COMPRESSED' : 0x03,
    'TILE_COMPRESSION' : 0x09,
    'NORMAL_NOCROP' : 0x41,
    'STORE_COMPRESSED_NOCROP' : 0x43,
    'TILE_COMPRESSION_NOCROP' : 0x49,
}
def get_real_sprite(sprite, pcx):
    global compression_flags
    if isinstance(sprite.compression, str):
        if not sprite.compression in compression_flags: raise ScriptError("Unknown real sprite compression:" + sprite.compression)
        return RealSpriteAction(sprite, pcx, compression_flags[sprite.compression])
    else: return RealSpriteAction(sprite, pcx)

