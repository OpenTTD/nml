from nml import generic, global_constants, expression
from nml.actions import action0
from nml.ast import base_statement

class CargoTable(base_statement.BaseStatement):
    def __init__(self, cargo_list, pos):
        base_statement.BaseStatement.__init__(self, "cargo table", pos, False, False)
        self.cargo_list = cargo_list
        generic.OnlyOnce.enforce(self, "cargo table")
        for i, cargo in enumerate(cargo_list):
            if isinstance(cargo, expression.Identifier):
                 self.cargo_list[i] = expression.StringLiteral(cargo.value, cargo.pos)
            expression.parse_string_to_dword(self.cargo_list[i])
            global_constants.cargo_numbers[self.cargo_list[i].value] = i

    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo.value

    def get_action_list(self):
        return action0.get_cargolist_action(self.cargo_list)

    def __str__(self):
        ret = 'cargotable {\n'
        ret += ', '.join([expression.identifier_to_print(cargo.value) for cargo in self.cargo_list])
        ret += '\n}\n'
        return ret
