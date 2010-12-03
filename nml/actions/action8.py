from nml import grfstrings
from nml.actions import base_action

class Action8(base_action.BaseAction):
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description

    def write(self, file):
        name = grfstrings.get_translation(self.name)
        desc = grfstrings.get_translation(self.description)
        size = 6 + grfstrings.get_string_size(name) + grfstrings.get_string_size(desc)
        file.start_sprite(size)
        file.print_bytex(8)
        file.print_bytex(7)
        file.print_string(self.grfid.value, False, True)
        file.print_string(name)
        file.print_string(desc)
        file.end_sprite()

    def skip_action7(self):
        return False
