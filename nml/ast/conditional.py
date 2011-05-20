from nml import global_constants
from nml.actions import action7
from nml.ast import general

class ConditionalList(object):
    """
    Wrapper for a complete if/else if/else if/else block.

    @ivar conditionals: List of blocks.
    @type conditionals: C{list} of L{Conditional}
    """
    def __init__(self, conditionals):
        self.conditionals = conditionals

    def pre_process(self):
        for cond in self.conditionals:
            cond.pre_process()

    def get_action_list(self):
        return action7.parse_conditional_block(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Conditional'
        for cond in self.conditionals:
            cond.debug_print(indentation + 2)

    def __str__(self):
        ret = ''
        for idx, cond in enumerate(self.conditionals):
            if idx > 0:
                str += ' else '
            ret += str(cond)
        ret += '\n'
        return ret

class Conditional(object):
    """
    Condition along with the code that has to be executed if the condition
    evaluates to some value not equal to 0.

    @ivar expr: The expression whre the executionof code in this block depends on.
    @type expr: L{Expression}

    @ivar block: List of AST-blocks that are to be conditionally executed.
    @type block: C{list} of AST-blocks.

    @ivar pos: Position information of this conditional block.
    @type pos: L{Position}
    """
    def __init__(self, expr, block, pos):
        self.expr = expr
        self.block = block
        self.pos = pos

    def pre_process(self):
        if self.expr is not None:
            self.expr = self.expr.reduce(global_constants.const_list)
        for b in self.block:
            b.pre_process()

    def debug_print(self, indentation):
        if self.expr is not None:
            print indentation*' ' + 'Expression:'
            self.expr.debug_print(indentation + 2)
        print indentation*' ' + 'Block:'
        general.print_script(self.block, indentation + 2)

    def __str__(self):
        ret = ''
        if self.expr is not None:
            ret += 'if (%s)' % str(self.expr)
        ret += ' {\n'
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret
