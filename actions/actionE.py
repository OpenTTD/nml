from generic import *

class ActionE:
    def __init__(self, grfid):
        self.grfid = ((grfid & 0xFF) << 24) | ((grfid & 0xFF00) << 8) | ((grfid & 0xFF0000) >> 8) | ((grfid & 0xFF000000) >> 24)
    
    def write(self, file):
        file.write("-1 * 0 0E 01 ")
        print_dwordx(file, self.grfid)
        file.write("\n\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
