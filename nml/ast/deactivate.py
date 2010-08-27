from nml.actions import actionE

class DeactivateBlock(object):
    def __init__(self, grfid_list, pos):
        self.grfid_list = [grfid.reduce() for grfid in grfid_list]
        self.pos = pos

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Deactivate other newgrfs:'
        for grfid in self.grfid_list:
            grfid.debug_print(indentation + 2)

    def get_action_list(self):
        return actionE.parse_deactivate_block(self)

    def __str__(self):
        return 'deactivate(%s);\n' % ', '.join([str(grfid) for grfid in self.grfid_list])
