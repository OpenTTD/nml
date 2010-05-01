from nml.generic import *
from nml.grfstrings import get_translation, get_string_size

class Action8:
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description
    
    def write(self, file):
        name = get_translation(self.name.name)
        desc = get_translation(self.description.name)
        size = 6 + get_string_size(name) + 3 + get_string_size(desc) + 3
        file.write(str(size) + " 08 07 ")
        print_string(file, self.grfid, False, True)
        print_string(file, name)
        print_string(file, desc)
        file.write("\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
