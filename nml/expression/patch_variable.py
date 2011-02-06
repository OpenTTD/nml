from nml import generic
from base_expression import Expression

class PatchVariable(Expression):
    """
    Class for reading so-called 'patch variables' via a special ActionD

    @ivar num: Variable number to read
    @type num: C{int}
    """
    def __init__(self, num, pos = None):
        Expression.__init__(self, pos)
        self.num = num

    def debug_print(self, indentation):
        print indentation*' ' + 'PatchVariable: ' + str(self.num)

    def __str__(self):
        return "PatchVariable(%d)" % self.num

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Reading patch variables is not supported in a switch-block.", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        return True
