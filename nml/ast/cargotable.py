from nml import global_constants
from nml.actions import action0

class CargoTable(object):
    def __init__(self, cargo_list, pos):
        self.cargo_list = cargo_list
        self.pos = pos
        for i, cargo in enumerate(cargo_list):
            global_constants.cargo_numbers[cargo.value] = i

    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo.value

    def get_action_list(self):
        return action0.get_cargolist_action(self.cargo_list)

    def __str__(self):
        ret = 'cargotable {\n'
        ret += ', '.join([cargo.value for cargo in self.cargo_list])
        ret += '\n}\n'
        return ret
