from nml.generic import *

class Action10:
    def __init__(self, label):
        self.label = label

    def prepare_output(self):
        pass

    def write(self, file):
        file.print_sprite_size(2)
        file.print_bytex(0x10)
        file.print_bytex(self.label)
        file.newline()
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False
