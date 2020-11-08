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
from nml.ast import assignment, base_statement


class BaseTracktypeTable(base_statement.BaseStatement):
    """Base class for RailtypeTable, RoadtypeTable etc."""

    def __init__(self, tracktype_list, pos):
        base_statement.BaseStatement.__init__(self, self.track_kind + "type table", pos, False, False)
        generic.OnlyOnce.enforce(self, self.track_kind + "type table")
        self.tracktype_table.clear()
        self.tracktype_list = tracktype_list

    def register_names(self):
        for i, tracktype in enumerate(self.tracktype_list):
            if isinstance(tracktype, assignment.Assignment):
                name = tracktype.name
                val_list = []
                for rt in tracktype.value:
                    if isinstance(rt, expression.Identifier):
                        val_list.append(expression.StringLiteral(rt.value, rt.pos))
                    else:
                        val_list.append(rt)
                    expression.parse_string_to_dword(
                        val_list[-1]
                    )  # we don't care about the result, only validate the input
                self.tracktype_list[i] = val_list if len(val_list) > 1 else val_list[0]
            else:
                name = tracktype
                if isinstance(tracktype, expression.Identifier):
                    self.tracktype_list[i] = expression.StringLiteral(tracktype.value, tracktype.pos)
                expression.parse_string_to_dword(
                    self.tracktype_list[i]
                )  # we don't care about the result, only validate the input
            self.tracktype_table[name.value] = i

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        generic.print_dbg(indentation, self.track_kind.title() + "type table")
        for tracktype in self.tracktype_list:
            if isinstance(tracktype, assignment.Assignment):
                generic.print_dbg(indentation + 2, self.track_kind.title() + ":", tracktype.name.value)
                for v in tracktype.value:
                    generic.print_dbg(indentation + 4, "Try:", v.value)
            else:
                generic.print_dbg(indentation + 2, self.track_kind.title() + ":", tracktype.value)

    def get_action_list(self):
        return action0.get_tracktypelist_action(
            self.table_prop_id, self.cond_tracktype_not_defined, self.tracktype_list
        )

    def __str__(self):
        lines = []
        for tracktype in self.tracktype_list:
            if isinstance(tracktype, assignment.Assignment):
                ids = [expression.identifier_to_print(v.value) for v in tracktype.value]
                lines.append("{}: [{}]".format(str(tracktype.name), ", ".join(ids)))
            else:
                lines.append(expression.identifier_to_print(tracktype.value))

        ret = self.track_kind + "typetable {\n    "
        ret += ", ".join(lines)
        ret += "\n}\n"
        return ret


class RailtypeTable(BaseTracktypeTable):
    track_kind = "rail"
    tracktype_table = global_constants.railtype_table
    table_prop_id = 0x12
    cond_tracktype_not_defined = 0x0D

    def __init__(self, *args, **kwargs):
        global_constants.is_default_railtype_table = False
        super().__init__(*args, **kwargs)


class RoadtypeTable(BaseTracktypeTable):
    track_kind = "road"
    tracktype_table = global_constants.roadtype_table
    table_prop_id = 0x16
    cond_tracktype_not_defined = 0x0F

    def __init__(self, *args, **kwargs):
        global_constants.is_default_roadtype_table = False
        super().__init__(*args, **kwargs)


class TramtypeTable(BaseTracktypeTable):
    track_kind = "tram"
    tracktype_table = global_constants.tramtype_table
    table_prop_id = 0x17
    cond_tracktype_not_defined = 0x11

    def __init__(self, *args, **kwargs):
        global_constants.is_default_tramtype_table = False
        super().__init__(*args, **kwargs)
