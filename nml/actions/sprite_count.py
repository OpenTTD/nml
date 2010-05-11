from nml.generic import *

class SpriteCountAction:
    def __init__(self, count):
        self.count = count
    
    def prepare_output(self):
        pass
    
    def write(self, file):
        file.write("4 ")
        print_dword(file, self.count)
        file.write("\n\n")
