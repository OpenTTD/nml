from nml.actions import action7

class SkipAll(object):
    """
    Skip everything after this statement.

    @ivar pos: Position information
    @type pos: L{Position}
    """
    def __init__(self, pos):
        self.pos = pos

    def register_names(self):
        pass

    def pre_process(self):
        pass

    def get_action_list(self):
        return [action7.UnconditionalSkipAction(9, 0)]

    def debug_print(self, indentation):
        print indentation*' ' + 'Skip all'

    def __str__(self):
        return "exit;\n"
