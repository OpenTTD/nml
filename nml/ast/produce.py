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

from nml import expression, generic
from nml.actions import action2, action2production, action2var
from nml.ast import base_statement

produce_base_class = action2.make_sprite_group_class(False, True, True)


class ProduceOld(produce_base_class):
    """
    AST node for a 'produce'-block, which is basically equivalent to the production callback.
    Syntax: produce(name, sub1, sub2, sub3, add1, add2[, again])
    @ivar param_list: List of parameters supplied to the produce-block.
                       - 0..2: Amounts of cargo to subtract from input
                       - 3..4: Amounts of cargo to add to output
                       - 5:    Run the production CB again if nonzero
    @type param_list: C{list} of L{Expression}
    """

    def __init__(self, param_list, pos):
        base_statement.BaseStatement.__init__(self, "produce-block", pos, False, False)
        if not (6 <= len(param_list) <= 7):
            raise generic.ScriptError(
                "produce-block requires 6 or 7 parameters, encountered {:d}".format(len(param_list)), self.pos
            )
        name = param_list[0]
        if not isinstance(name, expression.Identifier):
            raise generic.ScriptError("produce parameter 1 'name' should be an identifier.", name.pos)
        self.initialize(name, 0x0A)
        self.param_list = param_list[1:]
        if len(self.param_list) < 6:
            self.param_list.append(expression.ConstantNumeric(0))

    def pre_process(self):
        generic.print_warning("Consider using the new produce() syntax for '{}'".format(self.name), self.name.pos)
        for i, param in enumerate(self.param_list):
            self.param_list[i] = action2var.reduce_varaction2_expr(param, 0x0A)
        produce_base_class.pre_process(self)

    def collect_references(self):
        return []

    def __str__(self):
        return "produce({});\n".format(", ".join(str(x) for x in [self.name] + self.param_list))

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Produce, name =", self.name)
        generic.print_dbg(indentation + 2, "Subtract from input:")
        for expr in self.param_list[0:3]:
            expr.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Add to output:")
        for expr in self.param_list[3:5]:
            expr.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Again:")
        self.param_list[5].debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2production.get_production_actions(self)
        return []


class Produce(produce_base_class):
    """
    AST node for a 'produce'-block for version 2 industry production callback.
    Syntax: produce(name, [INP1: expression; ...], [OUT1: expression; ...], again)
        or: produce(name, [INP1: expression; ...], [OUT1: expression; ...])

    @ivar name: name given to this produce block
    @type name: L{Identifier}

    @ivar subtract_in: List of input cargos that are consumed for this production
                       (cargo label to register-expression mapping)
    @type subtract_in: C{list} of L{Assignment}

    @ivar add_out: List of output cargos that are generated for this production
                   (cargo label to register-expression mapping)
    @type add_out: C{list} of L{Assignment}

    @ivar again: Production CB is repeated if this is a register evaluating to nonzero
    @type again: L{Expression}
    """

    def __init__(self, name, subtract_in, add_out, again, pos):
        if not isinstance(name, expression.Identifier):
            raise generic.ScriptError("produce parameter 1 'name' should be an identifier.", name.pos)
        base_statement.BaseStatement.__init__(self, "produce-block", pos, False, False)
        self.initialize(name, 0x0A)
        self.subtract_in = subtract_in
        self.add_out = add_out
        self.again = again

    def pre_process(self):
        for i, param in enumerate(self.subtract_in):
            self.subtract_in[i].value = action2var.reduce_varaction2_expr(param.value, 0x0A)
        for i, param in enumerate(self.add_out):
            self.add_out[i].value = action2var.reduce_varaction2_expr(param.value, 0x0A)
        self.again = action2var.reduce_varaction2_expr(self.again, 0x0A)
        produce_base_class.pre_process(self)

    def collect_references(self):
        return []

    def __str__(self):
        return "produce({0}, [{1}], [{2}], {3})\n".format(
            str(self.name),
            " ".join(str(x) for x in self.subtract_in),
            " ".join(str(x) for x in self.add_out),
            str(self.again),
        )

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Produce, name =", self.name)
        for cargopair in self.subtract_in:
            generic.print_dbg(indentation + 2, "Subtract from input {0}:".format(cargopair.name.value))
            cargopair.value.debug_print(indentation + 4)
        for cargopair in self.add_out:
            generic.print_dbg(indentation + 2, "Add to output {0}:".format(cargopair.name.value))
            cargopair.value.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Again:")
        self.again.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2production.get_production_v2_actions(self)
        return []
