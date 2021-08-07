__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml import expression, generic, global_constants
from nml.actions import action0
from nml.ast import base_statement


class CargoTable(base_statement.BaseStatement):
    def __init__(self, cargo_list, pos):
        base_statement.BaseStatement.__init__(self, "cargo table", pos, False, False)
        self.cargo_list = cargo_list

    def register_names(self):
        generic.OnlyOnce.enforce(self, "cargo table")
        for i, cargo in enumerate(self.cargo_list):
            if isinstance(cargo, expression.Identifier):
                self.cargo_list[i] = expression.StringLiteral(cargo.value, cargo.pos)
            expression.parse_string_to_dword(
                self.cargo_list[i]
            )  # we don't care about the result, only validate the input
            if self.cargo_list[i].value in global_constants.cargo_numbers:
                generic.print_warning(
                    generic.Warning.GENERIC,
                    "Duplicate entry in cargo table: {}".format(self.cargo_list[i].value),
                    cargo.pos,
                )
            else:
                global_constants.cargo_numbers[self.cargo_list[i].value] = i

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Cargo table")
        for cargo in self.cargo_list:
            generic.print_dbg(indentation, "Cargo:", cargo.value)

    def get_action_list(self):
        return action0.get_cargolist_action(self.cargo_list)

    def __str__(self):
        ret = "cargotable {\n"
        ret += ", ".join([expression.identifier_to_print(cargo.value) for cargo in self.cargo_list])
        ret += "\n}\n"
        return ret
