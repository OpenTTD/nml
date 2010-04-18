from nml.generic import *
from nml.grfstrings import get_translation

class Action8:
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description
    
    def write(self, file):
        file.write("0 08 07 ")
        print_string(file, self.grfid, False, True)
        print_string(file, get_translation(self.name.name))
        print_string(file, get_translation(self.description.name))
        file.write("\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
