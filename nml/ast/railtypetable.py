from nml import generic, global_constants, expression
from nml.actions import action0

class RailtypeTable(object):
    def __init__(self, railtype_list, pos):
        self.railtype_list = railtype_list
        self.pos = pos
        generic.OnlyOnce.enforce(self, "rail type table")
        global_constants.railtype_table.clear()
        for i, railtype in enumerate(railtype_list):
            if isinstance(railtype, expression.Identifier):
                 self.railtype_list[i] = expression.StringLiteral(railtype.value, railtype.pos)
            expression.parse_string_to_dword(self.railtype_list[i])
            global_constants.railtype_table[self.railtype_list[i].value] = i

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Railtype table'
        for railtype in self.railtype_list:
            print (indentation+2)*' ' + 'Railtype:', railtype.value

    def get_action_list(self):
        return action0.get_railtypelist_action(self.railtype_list)

    def __str__(self):
        ret = 'railtypetable {\n'
        ret += ', '.join([expression.identifier_to_print(railtype.value) for railtype in self.railtype_list])
        ret += '\n}\n'
        return ret
