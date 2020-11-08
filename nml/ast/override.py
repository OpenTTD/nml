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


class EngineOverride(base_statement.BaseStatement):
    """
    AST Node for an engine override.

    @ivar grfid: GRFid of the grf to override the engines from.
    @type grfid: C{int{

    @ivar source_grfid: GRFid of the grf that overrides the engines.
    @type source_grfid: C{int}
    """

    def __init__(self, args, pos):
        base_statement.BaseStatement.__init__(self, "engine_override()", pos)
        self.args = args

    def pre_process(self):
        if len(self.args) not in (1, 2):
            raise generic.ScriptError("engine_override expects 1 or 2 parameters", self.pos)

        if len(self.args) == 1:
            try:
                self.source_grfid = expression.Identifier("GRFID").reduce(global_constants.const_list).value
                assert isinstance(self.source_grfid, int)
            except generic.ScriptError:
                raise generic.ScriptError("GRFID of this grf is required, but no grf-block is defined.", self.pos)
        else:
            self.source_grfid = expression.parse_string_to_dword(self.args[0].reduce(global_constants.const_list))

        self.grfid = expression.parse_string_to_dword(self.args[-1].reduce(global_constants.const_list))

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Engine override")
        generic.print_dbg(indentation, "Source:", self.source_grfid)
        generic.print_dbg(indentation, "Target:", self.grfid)

    def get_action_list(self):
        return action0.get_engine_override_action(self)

    def __str__(self):
        return "engine_override({});\n".format(", ".join(str(x) for x in self.args))
