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


class BadgeTable(base_statement.BaseStatement):
    def __init__(self, badge_list, pos):
        base_statement.BaseStatement.__init__(self, "badge table", pos, False, False)
        self.badge_list = badge_list

    def register_names(self):
        generic.OnlyOnce.enforce(self, "badge table")
        for i, badge in enumerate(self.badge_list):
            if isinstance(badge, expression.Identifier):
                self.badge_list[i] = expression.StringLiteral(badge.value, badge.pos)
            # expression.parse_string_to_dword(
            #     self.badge_list[i]
            # )  # we don't care about the result, only validate the input
            if self.badge_list[i].value in global_constants.badge_numbers:
                generic.print_warning(
                    generic.Warning.GENERIC,
                    "Duplicate entry in badge table: {}".format(self.badge_list[i].value),
                    badge.pos,
                )
            else:
                global_constants.badge_numbers[self.badge_list[i].value] = i

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Badge table")
        for badge in self.badge_list:
            generic.print_dbg(indentation, "Badge:", badge.value)

    def get_action_list(self):
        return action0.get_badgelist_action(self.badge_list)

    def __str__(self):
        ret = "badgetable {\n"
        ret += ", ".join([expression.identifier_to_print(badge.value) for badge in self.badge_list])
        ret += "\n}\n"
        return ret
