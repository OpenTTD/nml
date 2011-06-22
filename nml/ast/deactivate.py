from nml.actions import actionE
from nml.ast import base_statement

class DeactivateBlock(base_statement.BaseStatement):
    def __init__(self, grfid_list, pos):
        base_statement.BaseStatement.__init__(self, "deactivate()", pos)
        self.grfid_list = grfid_list

    def register_names(self):
        pass

    def pre_process(self):
        self.grfid_list = [grfid.reduce() for grfid in self.grfid_list]

    def debug_print(self, indentation):
        print indentation*' ' + 'Deactivate other newgrfs:'
        for grfid in self.grfid_list:
            grfid.debug_print(indentation + 2)

    def get_action_list(self):
        return actionE.parse_deactivate_block(self)

    def __str__(self):
        return 'deactivate(%s);\n' % ', '.join([str(grfid) for grfid in self.grfid_list])
