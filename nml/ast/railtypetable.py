from nml import global_constants
from nml.actions import action0

class RailtypeTable(object):
    def __init__(self, railtype_list, pos):
        self.railtype_list = railtype_list
        self.pos = pos
        global_constants.railtype_table.clear()
        for i, railtype in enumerate(railtype_list):
            global_constants.railtype_table[railtype.value] = i

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
        ret += ', '.join([railtype.value for railtype in self.railtype_list])
        ret += '\n}\n'
        return ret
