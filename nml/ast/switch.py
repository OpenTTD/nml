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
from nml.actions import action2, action2var, action2random
from nml.ast import base_statement, general

var_ranges = {
    'SELF' : 0x89,
    'PARENT' : 0x8A
}

# Used by Switch and RandomSwitch
switch_base_class = action2.make_sprite_group_class(False, True, True)

class Switch(switch_base_class):
    def __init__(self, param_list, body, pos):
        base_statement.BaseStatement.__init__(self, "switch-block", pos, False, False)
        if len(param_list) != 4:
            raise generic.ScriptError("Switch-block requires 4 parameters, encountered " + str(len(param_list)), pos)
        if not isinstance(param_list[1], expression.Identifier):
            raise generic.ScriptError("Switch-block parameter 2 'variable range' must be an identifier.", param_list[1].pos)
        if param_list[1].value in var_ranges:
            self.var_range = var_ranges[param_list[1].value]
        else:
            raise generic.ScriptError("Unrecognized value for switch parameter 2 'variable range': '{}'".format(param_list[1].value), param_list[1].pos)
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("Switch-block parameter 3 'name' must be an identifier.", param_list[2].pos)
        self.initialize(param_list[2], general.parse_feature(param_list[0]).value)
        self.expr = param_list[3]
        self.body = body

    def pre_process(self):
        var_feature = action2var.get_feature(self) # Feature of the accessed variables
        self.expr = action2var.reduce_varaction2_expr(self.expr, var_feature)
        self.body.reduce_expressions(var_feature)
        switch_base_class.pre_process(self)

    def collect_references(self):
        all_refs = self.expr.collect_references()
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if result is not None and result.value is not None:
                all_refs += result.value.collect_references()
        return all_refs

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Switch, Feature = {:d}, name = {}'.format(next(iter(self.feature_set)), self.name.value))

        generic.print_dbg(indentation + 2, 'Expression:')
        self.expr.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, 'Body:')
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2var.parse_varaction2(self)
        return []

    def __str__(self):
        var_range = 'SELF' if self.var_range == 0x89 else 'PARENT'
        return 'switch({}, {}, {}, {}) {{\n{}}}\n'.format(str(next(iter(self.feature_set))), var_range, str(self.name), str(self.expr), str(self.body))


class SwitchBody:
    """
    AST-node representing the body of a switch block
    This contains the various ranges as well as the default value

    @ivar ranges: List of ranges
    @type ranges: C{list} of L{SwitchRange}

    @ivar default: Default result to use if no range matches
    @type default: L{SwitchValue} or C{None} if N/A
    """
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def reduce_expressions(self, var_feature):
        for r in self.ranges[:]:
            if r.min is r.max and isinstance(r.min, expression.Identifier) and r.min.value == 'default':
                if self.default is not None:
                    raise generic.ScriptError("Switch-block has more than one default, which is impossible.", r.result.pos)
                self.default = r.result
                self.ranges.remove(r)
            else:
                r.reduce_expressions(var_feature)
        if self.default is not None and self.default.value is not None:
            self.default.value = action2var.reduce_varaction2_expr(self.default.value, var_feature)


    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        if self.default is not None:
            generic.print_dbg(indentation, 'Default:')
            self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = ''.join('\t{}\n'.format(r) for r in self.ranges)
        if self.default is not None:
            ret += '\t{}\n'.format(str(self.default))
        return ret

class SwitchRange:
    def __init__(self, min, max, result, unit = None):
        self.min = min
        self.max = max
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_feature):
        self.min = self.min.reduce(global_constants.const_list)
        self.max = self.max.reduce(global_constants.const_list)
        if self.result.value is not None:
            self.result.value = action2var.reduce_varaction2_expr(self.result.value, var_feature)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Min:')
        self.min.debug_print(indentation + 2)
        generic.print_dbg(indentation, 'Max:')
        self.max.debug_print(indentation + 2)
        generic.print_dbg(indentation, 'Result:')
        self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        ret += ': ' + str(self.result)
        return ret

class SwitchValue:
    """
    Class representing a single returned value or sprite group in a switch-block
    Also used for random-switch and graphics blocks

    @ivar value: Value to return
    @type value: L{Expression} or C{None}

    @ivar is_return: Whether the return keyword was present
    @type is_return: C{bool}

    @ivar pos: Position information
    @type pos: L{Position}
    """
    def __init__(self, value, is_return, pos):
        self.value = value
        self.is_return = is_return
        self.pos = pos

    def debug_print(self, indentation):
        if self.value is None:
            assert self.is_return
            generic.print_dbg(indentation, 'Return computed value')
        else:
            generic.print_dbg(indentation, 'Return value:' if self.is_return else 'Go to block:')
            self.value.debug_print(indentation + 2)

    def __str__(self):
        if self.value is None:
            assert self.is_return
            return 'return;'
        elif self.is_return:
            return 'return {};'.format(self.value)
        else:
            return '{};'.format(self.value)

class RandomSwitch(switch_base_class):
    def __init__(self, param_list, choices, pos):
        base_statement.BaseStatement.__init__(self, "random_switch-block", pos, False, False)
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError("random_switch requires 3 or 4 parameters, encountered {:d}".format(len(param_list)), pos)
        #feature
        feature = general.parse_feature(param_list[0]).value

        #type
        self.type = param_list[1]
        # Extract type name and possible argument
        if isinstance(self.type, expression.Identifier):
            self.type_count = None
        elif isinstance(self.type, expression.FunctionCall):
            if len(self.type.params) == 0:
                self.type_count = None
            elif len(self.type.params) == 1:
                self.type_count = action2var.reduce_varaction2_expr(self.type.params[0], feature)
            else:
                raise generic.ScriptError("Value for random_switch parameter 2 'type' can have only one parameter.", self.type.pos)
            self.type = self.type.name
        else:
            raise generic.ScriptError("random_switch parameter 2 'type' should be an identifier, possibly with a parameter.", self.type.pos)

        #name
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("random_switch parameter 3 'name' should be an identifier", pos)
        name = param_list[2]

        #triggers
        self.triggers = param_list[3] if len(param_list) == 4 else expression.ConstantNumeric(0)

        #body
        self.choices = []
        self.dependent = []
        self.independent = []
        for choice in choices:
            if isinstance(choice.probability, expression.Identifier):
                if choice.probability.value == 'dependent':
                    self.dependent.append(choice.result)
                    continue
                elif choice.probability.value == 'independent':
                    self.independent.append(choice.result)
                    continue
            self.choices.append(choice)
        if len(self.choices) == 0:
            raise generic.ScriptError("random_switch requires at least one possible choice", pos)

        self.initialize(name, feature)
        self.random_act2 = None # Set during action generation to resolve dependent/independent chains

    def pre_process(self):
        for choice in self.choices:
            choice.reduce_expressions(next(iter(self.feature_set)))

        for dep_list in (self.dependent, self.independent):
            for i, dep in enumerate(dep_list[:]):
                if dep.is_return:
                    raise generic.ScriptError("Expected a random_switch identifier after (in)dependent, not a return.", dep.pos)
                dep_list[i] = dep.value.reduce(global_constants.const_list)
                # Make sure, all [in]dependencies refer to existing random switch blocks
                if (not isinstance(dep_list[i], expression.SpriteGroupRef)) or len(dep_list[i].param_list) > 0:
                    raise generic.ScriptError("Value for (in)dependent should be an identifier", dep_list[i].pos)
                spritegroup = action2.resolve_spritegroup(dep_list[i].name)
                if not isinstance(spritegroup, RandomSwitch):
                    raise generic.ScriptError("Value of (in)dependent '{}' should refer to a random_switch.".format(dep_list[i].name.value), dep_list[i].pos)

        self.triggers = self.triggers.reduce_constant(global_constants.const_list)
        if not (0 <= self.triggers.value <= 255):
            raise generic.ScriptError("random_switch parameter 4 'triggers' out of range 0..255, encountered " + str(self.triggers.value), self.triggers.pos)

        switch_base_class.pre_process(self)


    def collect_references(self):
        all_refs = []
        for choice in self.choices:
            all_refs += choice.result.value.collect_references()
        return all_refs

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Random')
        generic.print_dbg(indentation + 2, 'Feature:', next(iter(self.feature_set)))
        generic.print_dbg(indentation + 2, 'Type:')
        self.type.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, 'Name:', self.name.value)

        generic.print_dbg(indentation + 2, 'Triggers:')
        self.triggers.debug_print(indentation + 4)
        for dep in self.dependent:
            generic.print_dbg(indentation + 2, 'Dependent on:')
            dep.debug_print(indentation + 4)
        for indep in self.independent:
            generic.print_dbg(indentation + 2, 'Independent from:')
            indep.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, 'Choices:')
        for choice in self.choices:
            choice.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2random.parse_randomswitch(self)
        return []

    def __str__(self):
        ret = 'random_switch({}, {}, {}, {}) {{\n'.format(str(next(iter(self.feature_set))), str(self.type), str(self.name), str(self.triggers))
        for dep in self.dependent:
            ret += 'dependent: {};\n'.format(dep)
        for indep in self.independent:
            ret += 'independent: {};\n'.format(indep)
        for choice in self.choices:
            ret += str(choice) + '\n'
        ret += '}\n'
        return ret

class RandomChoice:
    """
    Class to hold one of the possible choices in a random_switch

    @ivar probability: Relative chance for this choice to be chosen
    @type probability: L{Expression}

    @ivar result: Result of this choice, either another action2 or a return value
    @type result: L{SwitchValue}
    """
    def __init__ (self, probability, result):
        self.probability = probability
        if result.value is None:
            raise generic.ScriptError("Returning the computed value is not possible in a random_switch, as there is no computed value.", result.pos)
        self.result = result

    def reduce_expressions(self, var_feature):
        self.probability = self.probability.reduce_constant(global_constants.const_list)
        if self.probability.value <= 0:
            raise generic.ScriptError("Random probability must be higher than 0", self.probability.pos)
        self.result.value = action2var.reduce_varaction2_expr(self.result.value, var_feature)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Probability:')
        self.probability.debug_print(indentation + 2)

        generic.print_dbg(indentation, 'Result:')
        self.result.debug_print(indentation + 2)

    def __str__(self):
        return '{}: {}'.format(self.probability, self.result)

