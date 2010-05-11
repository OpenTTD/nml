from nml.generic import *

free_parameters = range(0x40, 0x80)
free_parameters.reverse()

class Action6:
    def __init__(self):
        self.modifications = []
        
    def modify_bytes(self, param, num_bytes, offset):
        self.modifications.append( (param, num_bytes, offset) )
    
    def prepare_output(self):
        pass
    
    def write(self, file):
        size = 2 + 5 * len(self.modifications)
        file.print_sprite_size(size)
        file.print_bytex(6)
        file.newline()
        for mod in self.modifications:
            file.print_bytex(mod[0])
            file.print_bytex(mod[1])
            file.print_bytex(0xFF)
            file.print_wordx(mod[2])
            file.newline()
        file.print_bytex(0xFF)
        file.newline()
        file.newline()
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

def reset_free_parameters(free_params):
    global free_parameters
    free_parameters = free_params
