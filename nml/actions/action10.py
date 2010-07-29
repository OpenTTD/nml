from nml.actions import base_action

class Action10(base_action.BaseAction):
    def __init__(self, label):
        self.label = label

    def write(self, file):
        file.start_sprite(2)
        file.print_bytex(0x10)
        file.print_bytex(self.label)
        file.newline()
        file.end_sprite()

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False
