from generic import *

free_parameters = range(0x40, 0x80)
free_parameters.reverse()

class Action6:
    def __init__(self):
        self.modifications = []
        
    def modify_bytes(self, param, num_bytes, offset):
        self.modifications.append( (param, num_bytes, offset) )
    
    def write(self, file):
        file.write("-1 * 0 06\n")
        for mod in self.modifications:
            print_bytex(file, mod[0])
            print_bytex(file, mod[1])
            print_bytex(file, 0xFF)
            print_wordx(file, mod[2])
            file.write("\n")
        file.write("FF\n\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
