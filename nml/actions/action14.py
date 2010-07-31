from nml import grfstrings
from nml.actions import base_action, action7


class Action14(base_action.BaseAction):
    def __init__(self, nodes):
        self.nodes = nodes

    def skip_action7(self):
        return False

    def write(self, file):
        size = 2 # final 0-byte
        for node in self.nodes: size += node.get_size()

        file.start_sprite(size)
        file.print_bytex(0x14)
        for node in self.nodes:
            node.write(file)
        file.print_bytex(0)

        file.end_sprite()


class Action14Node(object):
    def __init__(self, type_string, id):
        self.type_string = type_string
        self.id = id

    def get_size(self):
        """
        How many bytes will be written to the output file by L{write}?

        @return: The size (in bytes) of this node.
        """
        raise NotImplementedError('get_size must be implemented in Action14Node-subclass %r' % type(self))

    def write(self, file):
        """
        Write this node to the output file.

        @param file: The file to write the output to.
        """
        raise NotImplementedError('write must be implemented in Action14Node-subclass %r' % type(self))

    def write_type_id(self, file):
        file.print_string(self.type_string, False, True)
        if isinstance(self.id, basestring):
            file.print_string(self.id, False, True)
        else:
            file.print_dword(self.id)

class TextNode(Action14Node):
    def __init__(self, id, string):
        Action14Node.__init__(self, "T", id)
        self.string = string

    def get_size(self):
        size = 0
        for translation in grfstrings.grf_strings[self.string.name.value]:
            # 9 is for "T" (1), id (4), langid (1), thorn at start (2), final 0-byte (1)
            size += 9 + grfstrings.get_string_size(translation['text'])
        return size

    def write(self, file):
        for translation in grfstrings.grf_strings[self.string.name.value]:
            self.write_type_id(file)
            file.print_bytex(translation['lang'])
            file.print_string(translation['text'])
            file.newline()

class BranchNode(Action14Node):
    def __init__(self, id):
        Action14Node.__init__(self, "C", id)
        self.subnodes = []

    def get_size(self):
        size = 6 # "C", id, final 0-byte
        for node in self.subnodes:
            size += node.get_size()
        return size

    def write(self, file):
        self.write_type_id(file)
        file.newline()
        for node in self.subnodes:
            node.write(file)
        file.print_bytex(0)
        file.newline()

def grf_name_desc_actions(name, desc):
    root = BranchNode("INFO")
    if len(grfstrings.grf_strings[name.name.value]) > 1:
        name_node = TextNode("NAME", name)
        root.subnodes.append(name_node)
    if len(grfstrings.grf_strings[desc.name.value]) > 1:
        desc_node = TextNode("DESC", desc)
        root.subnodes.append(desc_node)
    if len(root.subnodes) > 0:
        skip_act = action7.SkipAction(9, 0x9D, 4, (2, r'\7='), 0, 1)
        return [skip_act, Action14([root])]
    return []
