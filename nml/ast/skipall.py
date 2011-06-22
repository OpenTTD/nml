from nml.actions import action7
from nml.ast import base_statement

class SkipAll(base_statement.BaseStatement):
    """
    Skip everything after this statement.
    """
    def __init__(self, pos):
        base_statement.BaseStatement.__init__(self, "exit-statement", pos)

    def get_action_list(self):
        return [action7.UnconditionalSkipAction(9, 0)]

    def debug_print(self, indentation):
        print indentation*' ' + 'Skip all'

    def __str__(self):
        return "exit;\n"
