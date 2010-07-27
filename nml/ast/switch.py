from nml import expression, generic, global_constants
from nml.actions import action2var, action2random
from nml.ast import general

var_ranges = {
    'SELF' : 0x89,
    'PARENT' : 0x8A
}

class Switch(object):
    def __init__(self, feature, var_range, name, expr, body, pos):
        self.feature = feature.reduce_constant([general.feature_ids])
        if var_range.value in var_ranges:
            self.var_range = var_ranges[var_range.value]
        else:
            raise generic.ScriptError("Unrecognized value for switch parameter 2 'variable range': '%s'" % var_range.value, var_range.pos)
        self.name = name
        self.expr = expr
        self.body = body
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =',self.feature.value,', name =', self.name.value
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        return action2var.parse_varaction2(self)

    def __str__(self):
        var_range = 'SELF' if self.var_range == 0x89 else 'PARENT'
        return 'switch(%s, %s, %s, %s) {\n%s}\n' % (str(self.feature), var_range, str(self.name), str(self.expr), str(self.body))


class SwitchBody(object):
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if isinstance(self.default, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.default.debug_print(indentation + 4);
        elif self.default is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = ''
        for r in self.ranges:
            ret += '\t%s\n' % str(r)
        if self.default is None:
            ret += '\treturn;\n'
        else:
            ret += '\t%s;\n' % str(self.default)
        return ret

class RandomSwitch(object):
    def __init__(self, param_list, choices, pos):
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError("random_switch requires 3 or 4 parameters, encountered %d" % len(param_list), pos)
        #feature
        self.feature = param_list[0].reduce_constant([general.feature_ids])

        #type
        self.type = param_list[1]

        #name
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("random_switch parameter 3 'name' should be an identifier", pos)
        self.name = param_list[2]

        #triggers
        self.triggers = param_list[3].reduce_constant(global_constants.const_list) if len(param_list) == 4 else expression.ConstantNumeric(0)
        if not (0 <= self.triggers.value <= 255):
            raise generic.ScriptError("random_switch parameter 4 'triggers' out of range 0..255, encountered " + str(self.triggers.value), self.triggers.pos)

        #body
        self.choices = []
        self.dependent = []
        self.independent = []
        for choice in choices:
            if isinstance(choice.probability, expression.Identifier):
                if choice.probability.value == 'independent':
                    if not isinstance(choice.result, expression.Identifier):
                        raise generic.ScriptError("Value for 'independent' should be an identifier")
                    self.independent.append(choice.result)
                    continue
                elif choice.probability.value == 'dependent':
                    if not isinstance(choice.result, expression.Identifier):
                        raise generic.ScriptError("Value for 'dependent' should be an identifier")
                    self.dependent.append(choice.result)
                    continue
                else:
                    assert 0, "NOT REACHED"
            self.choices.append(choice)
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Random'
        print (2+indentation)*' ' + 'Feature:', self.feature.value
        print (2+indentation)*' ' + 'Type:'
        self.type.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Name:', self.name.value
        print (2+indentation)*' ' + 'Triggers:'
        self.triggers.debug_print(indentation + 4)
        for dep in self.dependent:
            print (2+indentation)*' ' + 'Dependent on:', dep.value
        for indep in self.independent:
            print (2+indentation)*' ' + 'Independent from:', indep.value
        print (2+indentation)*' ' + 'Choices:'
        for choice in self.choices:
            choice.debug_print(indentation + 4)

    def get_action_list(self):
        return action2random.parse_randomswitch(self)

    def __str__(self):
        ret = 'random(%s, %s, %s, %s) {\n' % (str(self.feature), str(self.type), str(self.name), str(self.triggers))
        for dep in self.dependent:
            ret += 'dependent: %s;\n' % str(dep)
        for indep in self.independent:
            ret += 'independent: %s;\n' % str(indep)
        for choice in self.choices:
            ret += str(choice) + '\n'
        ret += '}\n'
        return ret
