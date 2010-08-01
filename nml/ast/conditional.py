from nml import global_constants
from nml.actions import action7
from nml.ast import general

class Conditional(object):
    def __init__(self, expr, block, else_block, pos):
        self.expr = expr
        if self.expr is not None:
            self.expr = self.expr.reduce(global_constants.const_list)
        self.block = block
        self.else_block = else_block
        self.pos = pos

    def pre_process(self):
        for b in self.block:
            b.pre_process()
        if self.else_block is not None:
            self.else_block.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'Conditional'
        if self.expr is not None:
            print (2+indentation)*' ' + 'Expression:'
            self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        general.print_script(self.block, indentation + 4)
        if self.else_block is not None:
            print (indentation)*' ' + 'Else block:'
            self.else_block.debug_print(indentation)

    def get_action_list(self):
        return action7.parse_conditional_block(self)

    def __str__(self):
        ret = ''
        if self.expr is not None:
            ret += 'if (%s) {\n' % str(self.expr)
        for b in self.block:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        if self.expr is not None:
            if self.else_block is not None:
                ret += '} else {\n'
                ret += str(self.else_block)
            ret += '}\n'
        return ret
