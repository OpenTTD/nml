from nml.generic import *

class SpriteCountAction(object):
    def __init__(self, count):
        self.count = count

    def prepare_output(self):
        pass

    def write(self, file):
        file.print_sprite_size(4)
        file.print_dword(self.count)
        file.newline()
        file.newline()
