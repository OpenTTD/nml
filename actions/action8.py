
class Action8:
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description
    
    def write(self, file):
        file.write("-1 * 0 08 07 ")
        self.grfid.write(file, False)
        file.write("\n")
        self.name.write(file)
        self.description.write(file)
        file.write("\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True
