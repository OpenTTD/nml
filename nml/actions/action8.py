from nml.generic import *
from nml.grfstrings import get_translation, get_string_size

class Action8:
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description
    
    def prepare_output(self):
        pass
    
    def write(self, file):
        name = get_translation(self.name.name)
        desc = get_translation(self.description.name)
        size = 6 + get_string_size(name) + 3 + get_string_size(desc) + 3
        file.print_sprite_size(size)
        file.print_bytex(8)
        file.print_bytex(7)
        file.print_string(self.grfid, False, True)
        file.print_string(name)
        file.print_string(desc)
        file.newline()
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
