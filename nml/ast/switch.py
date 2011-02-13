from nml import expression, generic, global_constants, nmlop
from nml.actions import action2, action2var, action2random, action2var_variables
from nml.ast import general

var_ranges = {
    'SELF' : 0x89,
    'PARENT' : 0x8A
}

# Used by Switch and RandomSwitch
switch_base_class = action2.make_sprite_group_class(action2.SpriteGroupRefType.SPRITEGROUP, action2.SpriteGroupRefType.SPRITEGROUP, action2.SpriteGroupRefType.SPRITEGROUP, True)

class Switch(switch_base_class):
    def __init__(self, feature, var_range, name, expr, body, pos):
        self.initialize(name, general.parse_feature(feature))
        if var_range.value in var_ranges:
            self.var_range = var_ranges[var_range.value]
        else:
            raise generic.ScriptError("Unrecognized value for switch parameter 2 'variable range': '%s'" % var_range.value, var_range.pos)
        self.expr = expr
        self.body = body
        self.pos = pos

    def pre_process(self):
        switch_base_class.pre_process(self)
        self.expr = action2var.reduce_varaction2_expr(self)

    def collect_references(self):
        all_refs = []
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if isinstance(result, action2.SpriteGroupRef) and result.name.value != 'CB_FAILED':
                all_refs.append(result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =',self.feature.value,', name =', self.name.value
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
        return 'switch(%s, %s, %s, %s) {\n%s}\n' % (str(self.feature), var_range, str(self.name), str(self.expr), str(self.body))


class SwitchBody(object):
    """
    AST-node representing the body of a switch block
    This contains the various ranges as well as the default value

    @ivar ranges: List of ranges
    @type ranges: C{list} of L{SwitchRange}

    @ivar default: Default result to use if no range matches
    @type default: L{SpriteGroupRef}, L{Expression} or C{None}, depending on the type of result.
    """
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if self.default is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = ''
        for r in self.ranges:
            ret += '\t%s\n' % str(r)
        if isinstance(self.default, action2.SpriteGroupRef):
            ret += '\t%s;\n' % str(self.default)
        elif self.default is None:
            ret += '\treturn;\n'
        else:
            ret += '\treturn %s;' % str(self.default)
        return ret

class RandomSwitch(switch_base_class):
    def __init__(self, param_list, choices, pos):
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError("random_switch requires 3 or 4 parameters, encountered %d" % len(param_list), pos)
        #feature
        feature = general.parse_feature(param_list[0])

        #type
        self.type = param_list[1]

        #name
        if not isinstance(param_list[2], expression.Identifier):
            raise generic.ScriptError("random_switch parameter 3 'name' should be an identifier", pos)
        name = param_list[2]

        #initialize base class
        self.initialize(name, feature)

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
                    if (not isinstance(choice.result, action2.SpriteGroupRef)) or len(choice.result.param_list) > 0:
                        raise generic.ScriptError("Value for 'independent' should be an identifier", choice.result.pos)
                    self.independent.append(choice.result)
                    continue
                elif choice.probability.value == 'dependent':
                    if (not isinstance(choice.result, action2.SpriteGroupRef)) or len(choice.result.param_list) > 0:
                        raise generic.ScriptError("Value for 'dependent' should be an identifier", choice.result.pos)
                    self.dependent.append(choice.result)
                    continue
                else:
                    assert False, "NOT REACHED"
            self.choices.append(choice)

        self.pos = pos
        self.random_action2 = None # set during parsing

    def pre_process(self):
        switch_base_class.pre_process(self)
        # Make sure, all [in]dependencies refer to existing random switch blocks
        for dep in self.dependent + self.independent:
            spritegroup = action2.resolve_spritegroup(dep.name)
            if not isinstance(spritegroup, RandomSwitch):
                raise generic.ScriptError("Value of (in)dependent '%s' should refer to a random_switch." % dep.name.value, dep.pos)

    def collect_references(self):
        all_refs = []
        for choice in self.choices:
            if isinstance(choice.result, action2.SpriteGroupRef) and choice.result.name.value != 'CB_FAILED':
                all_refs.append(choice.result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Random'
        print (2+indentation)*' ' + 'Feature:', self.feature.value
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
            return parse_randomswitch(self)
        return []

    def __str__(self):
        ret = 'random_switch(%s, %s, %s, %s) {\n' % (str(self.feature), str(self.type), str(self.name), str(self.triggers))
        for dep in self.dependent:
            ret += 'dependent: %s;\n' % str(dep)
        for indep in self.independent:
            ret += 'independent: %s;\n' % str(indep)
        for choice in self.choices:
            ret += str(choice) + '\n'
        ret += '}\n'
        return ret

num_random_bits = {
    0x00 : [8],
    0x01 : [8],
    0x02 : [8],
    0x03 : [8],
    0x04 : [16, 4],
    0x05 : [8],
    0x06 : [0],
    0x07 : [8],
    0x08 : [0],
    0x09 : [8],
    0x0A : [16],
    0x0B : [0],
    0x0C : [0],
    0x0D : [0],
    0x0E : [0],
    0x0F : [8],
    0x10 : [2],
    0x11 : [16, 4],
}

random_types = {
    'SELF' : {'type': 0x80, 'range': 0, 'param': 0},
    'PARENT' : {'type': 0x83, 'range': 0, 'param': 0},
    'TILE' : {'type': 0x80, 'range': 1, 'param': 0},
    'BACKWARD_SELF' : {'type': 0x84, 'range': 0, 'param': 1, 'value': 0x00},
    'FORWARD_SELF' : {'type': 0x84, 'range': 0, 'param': 1, 'value': 0x40},
    'BACKWARD_ENGINE' : {'type': 0x84, 'range': 0, 'param': 1, 'value': 0x80},
    'BACKWARD_SAMEID' : {'type': 0x84, 'range': 0, 'param': 1, 'value': 0xC0},
}

def parse_randomswitch_type(feature, type):
    """
    Parse the type of a random switch to determine the type and random bits to use.

    @param feature: Feature of this random switch
    @type feature: C{ConstantNumeric}

    @param type: Type of the random switch
    @type type: L{Expression}

    @return: A tuple containing the following (in order):
                - The type byte of the resulting random action2.
                - The type (bit 6+7) of the randomact2 <count>, None if N/A.
                - An expression making bit 0..3 of <count>, None if N/A.
                - The first random bit that should be used (often 0)
                - The number of random bits available
    @rtype: C{tuple} of (C{int}, C{int} or C{None}, L{Expression} or C{None}, C{int}, C{int})
    """
    # Extract type name and possible argument
    if isinstance(type, expression.Identifier):
        type_name = type.value
        type_param = None
    elif isinstance(type, expression.FunctionCall):
        type_name = type.name.value
        if len(type.params) == 0:
            type_param = None
        elif len(type.params) == 1:
            type_param = type.params[0]
        else:
            raise generic.ScriptError("Value for random_switch parameter 2 'type' can have only one parameter.", type.pos)
    else:
        raise generic.ScriptError("random_switch parameter 2 'type' should be an identifier, possibly with a parameter.", type.pos)

    # Validate type name / param combination
    if type_name not in random_types:
        raise generic.ScriptError("Unrecognized value for random_switch parameter 2 'type': " + type_name, type.pos)

    if type_param is None:
        # No param given
        if random_types[type_name]['param'] == 1:
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' requires a parameter." % type_name, type.pos)
        count_type = None
        count_expr = None
    else:
        # Param given
        if random_types[type_name]['param'] == 0:
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' should not have a parameter." % type_name, type.pos)
        if not (0 <= feature.value <= 3):
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' is valid only for vehicles." % type_name, type.pos)
        count_type = random_types[type_name]['value']
        count_expr = type_param

    # Determine type byte
    type = random_types[type_name]['type']
    bit_range = random_types[type_name]['range']
    assert (type == 0x84) == (count_type is not None)

    # Check that feature / type combination is valid
    feature_val = feature.value
    if feature_val not in num_random_bits:
        raise generic.ScriptError("Invalid feature for random_switch: " + str(feature_val), feature.pos)
    if type == 0x83: feature_val = action2var_variables.varact2parent_scope[feature_val]
    if feature_val is None:
        raise generic.ScriptError("Feature '%d' does not have a 'PARENT' scope." % feature.value, type.pos)
    if bit_range != 0 and feature_val not in (0x04, 0x11):
        raise generic.ScriptError("Type 'TILE' is only supported for stations and airport tiles.", type.pos)

    # Determine random bits to use
    bits_available = num_random_bits[feature_val][bit_range]
    start_bit = sum(num_random_bits[feature_val][0:bit_range])
    if bits_available == 0:
        raise generic.ScriptError("No random data is available for the given feature and scope, feature: " + str(feature_val), feature.pos)

    return type, count_type, count_expr, start_bit, bits_available

def parse_randomswitch_choices(random_switch):
    """
    Parse all choices of a randomswitch block,
    and determine the total probability and number of random choices needed.

    @param random_switch: RandomSwitch block to parse
    @type random_switch: L{RandomSwitch}

    @return: A tuple containing the following:
                - Total probability of all choices
                - Number of random choices that will be needed
    """
    #determine total probability
    total_prob = 0
    if len(random_switch.choices) == 0:
        raise generic.ScriptError("random_switch requires at least one possible choice", random_switch.pos)

    for choice in random_switch.choices:
        total_prob += choice.probability.value
        if isinstance(choice.result, expression.ConstantNumeric):
            choice.comment = "return %d;" % choice.result.value
        elif isinstance(choice.result, action2.SpriteGroupRef):
            choice.comment = choice.result.name.value + ';'
        else:
            raise generic.ScriptError("Invalid return value in random_switch.", choice.result.pos)
    assert total_prob > 0 # RandomChoice enforces that individual probabilities are > 0

    # How many random choices are needed ?
    # This is equal to total_prob rounded up to the nearest power of 2
    nrand = 1
    while nrand < total_prob: nrand <<= 1

    return total_prob, nrand

def lookup_random_action2(sg_ref):
    """
    Lookup a sprite group reference to find the corresponding random action2

    @param sg_ref: Reference to random action2
    @type sg_ref: L{SpriteGroupRef}

    @return: Random action2 corresponding to this sprite group, or None if N/A
    @rtype: L{Action2Random} or C{None}
    """
    spritegroup = action2.resolve_spritegroup(sg_ref.name)
    assert isinstance(spritegroup, RandomSwitch) # Already checked in pre-processing
    act2 = spritegroup.random_action2
    assert isinstance(act2, action2random.Action2Random)
    return act2

def parse_randomswitch_dependencies(random_switch, start_bit, bits_available, nrand):
    """
    Handle the dependencies between random chains to determine the random bits to use

    @param random_switch: Random switch to parse
    @type random_switch: L{RandomSwitch}

    @param start_bit: First available random bit
    @type start_bit: C{int}

    @param bits_available: Number of random bits available
    @type bits_available: C{int}

    @param nrand: Number of random choices to use
    @type nrand: C{int}

    @return: A tuple of two values:
                - The first random bit to use
                - The number of random choices to use. This may be higher the the original amount passed as paramter
    @rtype: C{tuple} of (C{int}, C{int})
    """
    #Dependent random chains
    act2_to_copy = None
    for dep in random_switch.dependent:
        act2 = lookup_random_action2(dep)
        if act2 is None: continue # May happen if said random switch is not used and therefore not parsed
        if act2_to_copy is not None:
            if act2_to_copy.randbit != act2.randbit:
                raise generic.ScriptError("random_switch '%s' cannot be dependent on both '%s' and '%s' as these are independent of eachother." %
                    (random_switch.name.value, act2_to_copy.name, act2.name), random_switch.pos)
            if act2_to_copy.nrand != act2.nrand:
                raise generic.ScriptError("random_switch '%s' cannot be dependent on both '%s' and '%s' as they don't use the same amount of random data." %
                    (random_switch.name.value, act2_to_copy.name, act2.name), random_switch.pos)
        else:
            act2_to_copy = act2

    if act2_to_copy is not None:
        randbit = act2_to_copy.randbit
        if nrand > act2_to_copy.nrand:
            raise generic.ScriptError("random_switch '%s' cannot be dependent on '%s' as it requires more random data." %
                (random_switch.name.value, act2_to_copy.name), random_switch.pos)
        nrand = act2_to_copy.nrand
    else:
        randbit = -1

    #INdependent random chains
    possible_mask = ((1 << bits_available) - 1) << start_bit
    for indep in random_switch.independent:
        act2 = lookup_random_action2(indep)
        if act2 is None: continue # May happen if said random switch is not used and therefore not parsed
        possible_mask &= ~((act2.nrand - 1) << act2.randbit)

    required_mask = nrand - 1
    if randbit != -1:
        #randbit has already been determined. Check that it is suitable
        if possible_mask & (required_mask << randbit) != (required_mask << randbit):
            raise generic.ScriptError("Combination of dependence on and independence from random_switches is not possible for random_switch '%s'." % random_switch.name.value, random_switch.pos)
    else:
        #find a suitable randbit
        for i in range(start_bit, bits_available + start_bit):
            if possible_mask & (required_mask << i) == (required_mask << i):
                randbit = i
                break
        else:
            raise generic.ScriptError("Independence of all given random_switches is not possible for random_switch '%s'." % random_switch.name.value, random_switch.pos)

    return randbit, nrand

def parse_randomswitch(random_switch):
    """
    Parse a randomswitch block into actions

    @param random_switch: RandomSwitch block to parse
    @type random_switch: L{RandomSwitch}

    @return: List of actions
    @rtype: C{list} of L{BaseAction}
    """
    type, count_type, count_expr, start_bit, bits_available = parse_randomswitch_type(random_switch.feature, random_switch.type)

    total_prob, nrand = parse_randomswitch_choices(random_switch)

    # Verify that enough random data is available
    if min(1 << bits_available, 0x80) < nrand:
        raise generic.ScriptError("The maximum sum of all random_switch probabilities is %d, encountered %d." % (min(1 << bits_available, 0x80), total_prob), random_switch.pos)

    randbit, nrand = parse_randomswitch_dependencies(random_switch, start_bit, bits_available, nrand)

    #divide the 'extra' probabilities in an even manner
    i = 0
    while i < (nrand - total_prob):
        best_choice = None
        best_ratio = 0
        for choice in random_switch.choices:
            #float division, so 9 / 10 = 0.9
            ratio = choice.probability.value / float(choice.resulting_prob + 1)
            if ratio > best_ratio:
                best_ratio = ratio
                best_choice = choice
        assert best_choice is not None
        best_choice.resulting_prob += 1
        i += 1

    #handle the 'count' parameter, if necessary
    need_varact2 = False
    if count_type is not None:
        try:
            expr = count_expr.reduce_constant(global_constants.const_list)
            if not (1 <= expr.value <= 15):
                need_varact2 = True
        except generic.ConstError:
            need_varact2 = True
        except generic.ScriptError:
            need_varact2 = True
        count = count_type
        name = random_switch.name.value
        if need_varact2:
            # our own name will be used by the varaction2 we're going to add
            name += '@random'
        else:
            # add the value to the 'count' parameter
            count |= expr.value
    else:
        count = None
        name = random_switch.name.value

    random_action2 = action2random.Action2Random(random_switch.feature.value, name, type, count, random_switch.triggers.value, randbit, nrand, random_switch.choices)
    action_list = [random_action2]
    random_switch.random_action2 = random_action2

    # Correctly add action2 references, do that now because we need to reference the random action2
    for choice in random_switch.choices:
        choice.comment = "(%d/%d) -> (%d/%d): " % (choice.probability.value, total_prob, choice.resulting_prob, nrand) + choice.comment
        if isinstance(choice.result, action2.SpriteGroupRef) and choice.result.name.value != 'CB_FAILED':
            action2.add_ref(choice.result, random_action2)

    if need_varact2:
        #Add varaction2 that stores count_expr in temporary register 0x100
        pos = random_switch.pos
        va2_feature = expression.ConstantNumeric(random_switch.feature.value)
        va2_range = expression.Identifier('SELF', pos)
        va2_name = expression.Identifier(random_switch.name.value, pos)
        va2_expr = expression.BinOp(nmlop.STO_TMP, count_expr, expression.ConstantNumeric(0x100))
        va2_body = SwitchBody([], action2.SpriteGroupRef(expression.Identifier(name, pos), [], pos))
        switch = Switch(va2_feature, va2_range, va2_name, va2_expr, va2_body, pos)
        action_list.extend(switch.get_action_list())
    return action_list
