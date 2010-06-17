from nml import grfstrings

class Action8(object):
    def __init__(self, grfid, name, description):
        self.grfid = grfid
        self.name = name
        self.description = description

    def prepare_output(self):
        pass

    def write(self, file):
        name = grfstrings.get_translation(self.name.name.value)
        desc = grfstrings.get_translation(self.description.name.value)
        size = 6 + grfstrings.get_string_size(name) + 3 + grfstrings.get_string_size(desc) + 3
        file.start_sprite(size)
        file.print_bytex(8)
        file.print_bytex(7)
        file.print_string(self.grfid.value, False, True)
        file.print_string(name)
        file.print_string(desc)
        file.end_sprite()

    def skip_action7(self):
        return False

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True
