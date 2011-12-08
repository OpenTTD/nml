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
            raise generic.ScriptError("Unrecognized value for switch parameter 2 'variable range': '%s'" % param_list[1].value, param_list[1].pos)
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
        all_refs = []
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if isinstance(result, expression.SpriteGroupRef):
                all_refs.append(result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature = %d, name = %s', (self.feature_set.copy().pop(), self.name.value)
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_output():
            return action2var.parse_varaction2(self)
        return []

    def __str__(self):
        var_range = 'SELF' if self.var_range == 0x89 else 'PARENT'
        return 'switch(%s, %s, %s, %s) {\n%s}\n' % (str(self.feature_set.copy().pop()), var_range, str(self.name), str(self.expr), str(self.body))


class SwitchBody(object):
    """
    AST-node representing the body of a switch block
    This contains the various ranges as well as the default value

    @ivar ranges: List of ranges
    @type ranges: C{list} of L{SwitchRange}

    @ivar default: Default result to use if no range matches
    @type default: L{SpriteGroupRef}, L{Expression} or C{None} (before pre-processing only), depending on the type of result.
    """
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def reduce_expressions(self, var_feature):
        if self.default is not None:
            self.default = action2var.reduce_varaction2_expr(self.default, var_feature)
        for r in self.ranges:
            r.reduce_expressions(var_feature)

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if self.default is not None:
            self.default.debug_print(indentation + 2)
        else:
            print (indentation+2)*' ' + 'Return computed value'

    def __str__(self):
        ret = ''
        for r in self.ranges:
            ret += '\t%s\n' % str(r)
        if self.default is None:
            ret += '\treturn;\n'
        elif isinstance(self.default, expression.SpriteGroupRef):
            ret += '\t%s;\n' % str(self.default)
        else:
            ret += '\treturn %s;\n' % str(self.default)
        return ret

class SwitchRange(object):
    def __init__(self, min, max, result, unit = None):
        self.min = min
        self.max = max
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_feature):
        self.min = self.min.reduce(global_constants.const_list)
        self.max = self.max.reduce(global_constants.const_list)
        if self.result is not None:
            self.result = action2var.reduce_varaction2_expr(self.result, var_feature)

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if self.result is not None:
            self.result.debug_print(indentation + 2)
        else:
            print (indentation+2)*' ' + 'Return computed value'

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if self.result is None:
            ret += ': return;'
        elif isinstance(self.result, expression.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret

class RandomSwitch(switch_base_class):
    def __init__(self, param_list, choices, pos):
        base_statement.BaseStatement.__init__(self, "random_switch-block", pos, False, False)
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError("random_switch requires 3 or 4 parameters, encountered %d" % len(param_list), pos)
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
            choice.reduce_expressions(self.feature_set.copy().pop())

        for dep_list in (self.dependent, self.independent):
            for i, dep in enumerate(dep_list[:]):
                dep_list[i] = dep.reduce(global_constants.const_list)
                # Make sure, all [in]dependencies refer to existing random switch blocks
                if (not isinstance(dep_list[i], expression.SpriteGroupRef)) or len(dep_list[i].param_list) > 0:
                    raise generic.ScriptError("Value for (in)dependent should be an identifier", dep_list[i].pos)
                spritegroup = action2.resolve_spritegroup(dep_list[i].name)
                if not isinstance(spritegroup, RandomSwitch):
                    raise generic.ScriptError("Value of (in)dependent '%s' should refer to a random_switch." % dep_list[i].name.value, dep_list[i].pos)

        self.triggers = self.triggers.reduce_constant(global_constants.const_list)
        if not (0 <= self.triggers.value <= 255):
            raise generic.ScriptError("random_switch parameter 4 'triggers' out of range 0..255, encountered " + str(self.triggers.value), self.triggers.pos)

        switch_base_class.pre_process(self)


    def collect_references(self):
        all_refs = []
        for choice in self.choices:
            if isinstance(choice.result, expression.SpriteGroupRef):
                all_refs.append(choice.result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Random'
        print (2+indentation)*' ' + 'Feature:', self.feature_set.copy().pop()
        print (2+indentation)*' ' + 'Type:'
        self.type.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Name:', self.name.value
        print (2+indentation)*' ' + 'Triggers:'
        self.triggers.debug_print(indentation + 4)
        for dep in self.dependent:
            print (2+indentation)*' ' + 'Dependent on:'
            dep.debug_print(indentation + 4)
        for indep in self.independent:
            print (2+indentation)*' ' + 'Independent from:'
            indep.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Choices:'
        for choice in self.choices:
            choice.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_output():
            return action2random.parse_randomswitch(self)
        return []

    def __str__(self):
        ret = 'random_switch(%s, %s, %s, %s) {\n' % (str(self.feature_set.copy().pop()), str(self.type), str(self.name), str(self.triggers))
        for dep in self.dependent:
            ret += 'dependent: %s;\n' % str(dep)
        for indep in self.independent:
            ret += 'independent: %s;\n' % str(indep)
        for choice in self.choices:
            ret += str(choice) + '\n'
        ret += '}\n'
        return ret

class RandomChoice(object):
    """
    Class to hold one of the possible choices in a random_switch

    @ivar probability: Relative chance for this choice to be chosen
    @type probability: L{Expression}

    @ivar result: Result of this choice, either another action2 or a return value
    @type result: L{SpriteGroupRef} or L{Expression}
    """
    def __init__ (self, probability, result):
        self.probability = probability
        if result is None:
            raise generic.ScriptError("Returning the computed value is not possible in a random_switch, as there is no computed value.", self.probability.pos)
        self.result = result

    def reduce_expressions(self, var_feature):
        self.probability = self.probability.reduce_constant(global_constants.const_list)
        if self.probability.value <= 0:
            raise generic.ScriptError("Random probability must be higher than 0", self.probability.pos)
        self.result = action2var.reduce_varaction2_expr(self.result, var_feature)

    def debug_print(self, indentation):
        print indentation*' ' + 'Probability:'
        self.probability.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.probability)
        if isinstance(self.result, expression.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret

