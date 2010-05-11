from nml.generic import *

class Action10:
    def __init__(self, label):
        self.label = label
    
    def prepare_output(self):
        pass
    
    def write(self, file):
        file.write("2 10 ")
        print_bytex(file, self.label)
        file.write("\n\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return False
    
    def skip_needed(self):
        return False
