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
from nml.actions import action2, action2random, action2var
from nml.ast import base_statement, general

var_ranges = {"SELF": 0x89, "PARENT": 0x8A}

# Used by Switch and RandomSwitch
switch_base_class = action2.make_sprite_group_class(False, True, True)


class Switch(switch_base_class):
    def __init__(self, param_list, body, pos):
        base_statement.BaseStatement.__init__(self, "switch-block", pos, False, False)
        if len(param_list) < 4:
            raise generic.ScriptError(
                "Switch-block requires at least 4 parameters, encountered " + str(len(param_list)), pos
            )
        if not isinstance(param_list[1], expression.Identifier):
            raise generic.ScriptError(
                "Switch-block parameter 2 'variable range' must be an identifier.", param_list[1].pos
            )
        if param_list[1].value in var_ranges:
            self.var_range = var_ranges[param_list[1].value]
        else:
            raise generic.ScriptError(
                "Unrecognized value for switch parameter 2 'variable range': '{}'".format(param_list[1].value),
                param_list[1].pos,
            )
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("Switch-block parameter 3 'name' must be an identifier.", param_list[2].pos)
        self.initialize(param_list[2], general.parse_feature(param_list[0]).value, len(param_list) - 4)
        self.expr = param_list[-1]
        self.body = body
        self.param_list = param_list[3:-1]
        # register_map is a dict to be duck-compatible with spritelayouts.
        # But because feature_set has only one item for switches, register_map also has at most one item.
        self.register_map = {}

    def pre_process(self):
        # Check parameter names
        seen_names = set()
        for param in self.param_list:
            if not isinstance(param, expression.Identifier):
                raise generic.ScriptError("switch parameter names must be identifiers.", param.pos)
            if param.value in seen_names:
                raise generic.ScriptError("Duplicate parameter name '{}' encountered.".format(param.value), param.pos)
            seen_names.add(param.value)

        feature = next(iter(self.feature_set))
        var_scope = action2var.get_scope(feature, self.var_range)
        if var_scope is None:
            raise generic.ScriptError("Requested scope not available for this feature.", self.pos)

        # Allocate registers
        param_map = {}
        param_registers = []
        for param in self.param_list:
            reg = action2var.VarAction2CallParam(param.value)
            param_registers.append(reg)
            param_map[param.value] = reg
        param_map = (param_map, lambda name, value, pos: action2var.VarAction2LoadCallParam(value, name))
        self.register_map[feature] = param_registers

        self.expr = action2var.reduce_varaction2_expr(self.expr, var_scope, [param_map])
        self.body.reduce_expressions(var_scope, [param_map])
        switch_base_class.pre_process(self)

    def optimise(self):
        if self.optimised:
            return self.optimised is not self

        # Constant condition, pick the right result
        if isinstance(self.expr, expression.ConstantNumeric):
            for r in self.body.ranges[:]:
                if r.min.value <= self.expr.value <= r.max.value:
                    self.optimised = r.result.value if r.result.value else self.expr
            if not self.optimised and self.body.default:
                self.optimised = self.body.default.value if self.body.default.value else self.expr

        # Default result only
        if not self.optimised and self.expr.is_read_only() and self.body.default and len(self.body.ranges) == 0:
            self.optimised = self.body.default.value

        # If we return an expression, just rewrite ourself to keep the correct scope
        # so a return action with the wrong scope doesn't need to be created later
        if (
            self.optimised
            and not isinstance(self.optimised, expression.ConstantNumeric)
            and not (isinstance(self.optimised, expression.SpriteGroupRef) and not self.optimised.is_procedure)
            and not isinstance(self.optimised, expression.String)
        ):
            self.expr = self.optimised
            self.body.ranges = []
            self.body.default = SwitchValue(None, True, self.optimised.pos)
            self.optimised = self

        if self.optimised:
            generic.print_warning(
                generic.Warning.OPTIMISATION,
                "Block '{}' returns a constant, optimising.".format(self.name.value),
                self.pos,
            )
            return self.optimised is not self

        self.optimised = self  # Prevent multiple run on the same non optimisable Switch
        return False

    def collect_references(self):
        all_refs = self.expr.collect_references()
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if result is not None and result.value is not None:
                all_refs += result.value.collect_references()
        return all_refs

    def is_read_only(self):
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if result is not None and result.value is not None:
                if not result.value.is_read_only():
                    return False
        return self.expr.is_read_only()

    def debug_print(self, indentation):
        generic.print_dbg(
            indentation, "Switch, Feature = {:d}, name = {}".format(next(iter(self.feature_set)), self.name.value)
        )

        if self.param_list:
            generic.print_dbg(indentation + 2, "Parameters:")
            for param in self.param_list:
                param.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, "Expression:")
        self.expr.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, "Body:")
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2var.parse_varaction2(self)
        return []

    def __str__(self):
        var_range = "SELF" if self.var_range == 0x89 else "PARENT"
        params = "" if not self.param_list else "{}, ".format(", ".join(str(x) for x in self.param_list))
        return "switch({}, {}, {}, {}{}) {{\n{}}}\n".format(
            next(iter(self.feature_set)), var_range, self.name, params, self.expr, self.body
        )


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

    def reduce_expressions(self, var_scope, extra_dicts=None):
        if extra_dicts is None:
            extra_dicts = []
        for r in self.ranges[:]:
            if r.min is r.max and isinstance(r.min, expression.Identifier) and r.min.value == "default":
                if self.default is not None:
                    raise generic.ScriptError(
                        "Switch-block has more than one default, which is impossible.", r.result.pos
                    )
                self.default = r.result
                self.ranges.remove(r)
            else:
                r.reduce_expressions(var_scope, extra_dicts)
        if self.default is not None:
            if self.default.value is not None:
                self.default.value = action2var.reduce_varaction2_expr(self.default.value, var_scope, extra_dicts)
            if len(self.ranges) != 0:
                if any(self.default.value != r.result.value for r in self.ranges):
                    return
                generic.print_warning(
                    generic.Warning.OPTIMISATION,
                    "Switch-Block ranges are the same as default, optimising.",
                    self.default.pos,
                )
                self.ranges = []

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        if self.default is not None:
            generic.print_dbg(indentation, "Default:")
            self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = "".join("\t{}\n".format(r) for r in self.ranges)
        if self.default is not None:
            ret += "\t{}\n".format(str(self.default))
        return ret


class SwitchRange:
    def __init__(self, min, max, result, unit=None):
        self.min = min
        self.max = max
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_scope, extra_dicts=None):
        if extra_dicts is None:
            extra_dicts = []
        self.min = self.min.reduce(global_constants.const_list)
        self.max = self.max.reduce(global_constants.const_list)
        if self.result.value is not None:
            self.result.value = action2var.reduce_varaction2_expr(self.result.value, var_scope, extra_dicts)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Min:")
        self.min.debug_print(indentation + 2)
        generic.print_dbg(indentation, "Max:")
        self.max.debug_print(indentation + 2)
        generic.print_dbg(indentation, "Result:")
        self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if self.min is not self.max and (
            not isinstance(self.min, expression.ConstantNumeric)
            or not isinstance(self.max, expression.ConstantNumeric)
            or self.max.value != self.min.value
        ):
            ret += ".." + str(self.max)
        ret += ": " + str(self.result)
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
            generic.print_dbg(indentation, "Return computed value")
        else:
            generic.print_dbg(indentation, "Return value:" if self.is_return else "Go to block:")
            self.value.debug_print(indentation + 2)

    def __str__(self):
        if self.value is None:
            assert self.is_return
            return "return;"
        elif self.is_return:
            return "return {};".format(self.value)
        else:
            return "{};".format(self.value)


class RandomSwitch(switch_base_class):
    def __init__(self, param_list, choices, pos):
        base_statement.BaseStatement.__init__(self, "random_switch-block", pos, False, False)
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError(
                "random_switch requires 3 or 4 parameters, encountered {:d}".format(len(param_list)), pos
            )
        # feature
        feature = general.parse_feature(param_list[0]).value

        # type
        self.type = param_list[1]
        # Extract type name and possible argument
        if isinstance(self.type, expression.Identifier):
            self.type_count = None
        elif isinstance(self.type, expression.FunctionCall):
            if len(self.type.params) == 0:
                self.type_count = None
            elif len(self.type.params) == 1:
                # var_scope is really weird for type=BACKWARD/FORWARD.
                var_scope = action2var.get_scope(feature, 0x89)
                self.type_count = action2var.reduce_varaction2_expr(self.type.params[0], var_scope)
            else:
                raise generic.ScriptError(
                    "Value for random_switch parameter 2 'type' can have only one parameter.", self.type.pos
                )
            self.type = self.type.name
        else:
            raise generic.ScriptError(
                "random_switch parameter 2 'type' should be an identifier, possibly with a parameter.", self.type.pos
            )

        # name
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("random_switch parameter 3 'name' should be an identifier", pos)
        name = param_list[2]

        # triggers
        self.triggers = param_list[3] if len(param_list) == 4 else expression.ConstantNumeric(0)

        # body
        self.choices = []
        self.dependent = []
        self.independent = []
        for choice in choices:
            if isinstance(choice.probability, expression.Identifier):
                if choice.probability.value == "dependent":
                    self.dependent.append(choice.result)
                    continue
                elif choice.probability.value == "independent":
                    self.independent.append(choice.result)
                    continue
            self.choices.append(choice)
        if len(self.choices) == 0:
            raise generic.ScriptError("random_switch requires at least one possible choice", pos)

        self.initialize(name, feature)
        self.random_act2 = None  # Set during action generation to resolve dependent/independent chains

    def pre_process(self):
        feature = next(iter(self.feature_set))
        # var_scope is really weird for type=BACKWARD/FORWARD.
        # Expressions in cases will still refer to the origin vehicle.
        var_scope = action2var.get_scope(feature, 0x8A if self.type.value == "PARENT" else 0x89)

        for choice in self.choices:
            choice.reduce_expressions(var_scope)

        for dep_list in (self.dependent, self.independent):
            for i, dep in enumerate(dep_list[:]):
                if dep.is_return:
                    raise generic.ScriptError(
                        "Expected a random_switch identifier after (in)dependent, not a return.", dep.pos
                    )
                dep_list[i] = dep.value.reduce(global_constants.const_list)
                # Make sure, all [in]dependencies refer to existing random switch blocks
                if (not isinstance(dep_list[i], expression.SpriteGroupRef)) or len(dep_list[i].param_list) > 0:
                    raise generic.ScriptError("Value for (in)dependent should be an identifier", dep_list[i].pos)
                spritegroup = action2.resolve_spritegroup(dep_list[i].name)
                if not isinstance(spritegroup, RandomSwitch):
                    raise generic.ScriptError(
                        "Value of (in)dependent '{}' should refer to a random_switch.".format(dep_list[i].name.value),
                        dep_list[i].pos,
                    )

        self.triggers = self.triggers.reduce_constant(global_constants.const_list)
        if not (0 <= self.triggers.value <= 255):
            raise generic.ScriptError(
                "random_switch parameter 4 'triggers' out of range 0..255, encountered " + str(self.triggers.value),
                self.triggers.pos,
            )

        switch_base_class.pre_process(self)

    def optimise(self):
        if self.optimised:
            return self.optimised is not self

        # Triggers have side-effects, and can't be skipped.
        # Scope for expressions can be different in referencing location, so don't optimise them.
        if self.triggers.value == 0 and len(self.choices) == 1:
            optimised = self.choices[0].result.value
            if (
                isinstance(optimised, expression.ConstantNumeric)
                or (isinstance(optimised, expression.SpriteGroupRef) and not optimised.is_procedure)
                or isinstance(optimised, expression.String)
            ):
                generic.print_warning(
                    generic.Warning.OPTIMISATION,
                    "Block '{}' returns a constant, optimising.".format(self.name.value),
                    self.pos,
                )
                self.optimised = optimised
                return True

        self.optimised = self  # Prevent multiple run on the same non optimisable RandomSwitch
        return False

    def collect_references(self):
        all_refs = []
        for choice in self.choices:
            all_refs += choice.result.value.collect_references()
        return all_refs

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Random")
        generic.print_dbg(indentation + 2, "Feature:", next(iter(self.feature_set)))
        generic.print_dbg(indentation + 2, "Type:")
        self.type.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Name:", self.name.value)

        generic.print_dbg(indentation + 2, "Triggers:")
        self.triggers.debug_print(indentation + 4)
        for dep in self.dependent:
            generic.print_dbg(indentation + 2, "Dependent on:")
            dep.debug_print(indentation + 4)
        for indep in self.independent:
            generic.print_dbg(indentation + 2, "Independent from:")
            indep.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, "Choices:")
        for choice in self.choices:
            choice.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action2random.parse_randomswitch(self)
        return []

    def __str__(self):
        ret = "random_switch({}, {}, {}, {}) {{\n".format(
            str(next(iter(self.feature_set))), str(self.type), str(self.name), str(self.triggers)
        )
        for dep in self.dependent:
            ret += "dependent: {};\n".format(dep)
        for indep in self.independent:
            ret += "independent: {};\n".format(indep)
        for choice in self.choices:
            ret += str(choice) + "\n"
        ret += "}\n"
        return ret


class RandomChoice:
    """
    Class to hold one of the possible choices in a random_switch

    @ivar probability: Relative chance for this choice to be chosen
    @type probability: L{Expression}

    @ivar result: Result of this choice, either another action2 or a return value
    @type result: L{SwitchValue}
    """

    def __init__(self, probability, result):
        self.probability = probability
        if result.value is None:
            raise generic.ScriptError(
                "Returning the computed value is not possible in a random_switch, as there is no computed value.",
                result.pos,
            )
        self.result = result

    def reduce_expressions(self, var_scope):
        self.probability = self.probability.reduce_constant(global_constants.const_list)
        if self.probability.value <= 0:
            raise generic.ScriptError("Random probability must be higher than 0", self.probability.pos)
        self.result.value = action2var.reduce_varaction2_expr(self.result.value, var_scope)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Probability:")
        self.probability.debug_print(indentation + 2)

        generic.print_dbg(indentation, "Result:")
        self.result.debug_print(indentation + 2)

    def __str__(self):
        return "{}: {}".format(self.probability, self.result)
