from nml.actions import action7
from nml.ast import general
from nml import global_constants

class Loop(object):
    """
    AST node for a while-loop.

    @ivar expr: The conditional to check whether the loop continues.
    @type expr: L{Expression}

    @ivar block: List of AST-blocks that are to be conditionally executed.
    @type block: C{list} of AST-blocks.

    @ivar pos: Position information.
    @type pos: L{Position}
    """
    def __init__(self, expr, block, pos):
        self.expr = expr
        self.block = block
        self.pos = pos

    def register_names(self):
        for b in self.block:
            b.register_names()

    def pre_process(self):
        self.expr = self.expr.reduce(global_constants.const_list)
        for b in self.block:
            b.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'While loop'
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        general.print_script(self.block, indentation + 4)

    def get_action_list(self):
        return action7.parse_loop_block(self)

    def __str__(self):
        ret = 'while(%s) {\n' % self.expr
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret
