from nml.actions import action7
from nml.ast import general

class Loop(object):
    def __init__(self, expr, block, pos):
        self.expr = expr
        self.block = block
        self.pos = pos

    def pre_process(self):
        pass

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
