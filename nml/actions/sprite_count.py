from nml.generic import *

class SpriteCountAction:
    def write(self, file):
        file.write("4 ")
        print_dword(file, self.count)
        file.write("\n\n")
