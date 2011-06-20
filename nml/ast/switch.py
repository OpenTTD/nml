from nml import expression, generic, global_constants, nmlop
from nml.actions import action2, action2var, action2random, action2var_variables, action6
from nml.ast import general, switch_range

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
        self.return_switches = []

    def register_names(self):
        pass

    def add_extra_ret_switch(self, name, expr):
        return_name = expression.Identifier(name, self.pos)
        return_var_range = expression.Identifier('SELF', self.pos)
        # Set result to None, it will be parsed correctly during preprocessing
        return_body = SwitchBody([], None)
        self.return_switches.append(Switch(self.feature, return_var_range, return_name, expr, return_body, self.pos))
        self.return_switches[-1].pre_process()
        return action2.SpriteGroupRef(return_name, [], self.pos)

    def pre_process(self):
        self.expr = action2var.reduce_varaction2_expr(self.expr, action2var.get_feature(self))

        self.body.pre_process()

        num_extra_acts = 0
        for range in self.body.ranges:
            if range.result is not None and not isinstance(range.result, (action2.SpriteGroupRef, expression.String)) and not range.result.supported_by_actionD(False):
                range.result = self.add_extra_ret_switch('%s@ret%d' % (self.name.value, num_extra_acts), range.result)
                num_extra_acts += 1
        if self.body.default is not None and not isinstance(self.body.default, (action2.SpriteGroupRef, expression.String)) and not self.body.default.supported_by_actionD(False):
            self.body.default = self.add_extra_ret_switch('%s@ret%d' % (self.name.value, num_extra_acts), self.body.default)

        if any(map(lambda x: x is None, [r.result for r in self.body.ranges] + [self.body.default])):
            if len(self.body.ranges) == 0:
                # We already have no ranges, so can just add a bogus default result
                assert self.body.default is None
                self.body.default = action2.SpriteGroupRef(expression.Identifier('CB_FAILED', self.pos), [], self.pos)
            else:
                # Load var 0x1C, which is the last computed value. 
                return_expr = expression.Variable(expression.ConstantNumeric(0x1C, self.pos), pos=self.pos)
                ref = self.add_extra_ret_switch('%s@return' % self.name.value, return_expr)

                # Now replace any 'None' result with a reference to the result action
                for range in self.body.ranges:
                    if range.result is None:
                        range.result = ref
                if self.body.default is None:
                    self.body.default = ref
        elif len(self.body.ranges) == 0:
            # Avoid triggering the 'return computed value' special case
            self.body.ranges.append(switch_range.SwitchRange(expression.ConstantNumeric(0, self.pos), expression.ConstantNumeric(0, self.pos), self.body.default))

        # Now pre-process ourselves
        switch_base_class.pre_process(self)

    def collect_references(self):
        all_refs = []
        for result in [r.result for r in self.body.ranges] + [self.body.default]:
            if isinstance(result, action2.SpriteGroupRef) and result.name.value != 'CB_FAILED':
                all_refs.append(result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =',self.feature.value,', name =', self.name.value
        for ret_swich in self.return_switches:
            print (2+indentation)*' ' + 'Extra switch to return computed value:'
            ret_switch.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

    def get_action_list(self):
        action_list = []
        if self.prepare_output():
            for ret_switch in self.return_switches:
                action_list.extend(ret_switch.get_action_list())
            action_list.extend(action2var.parse_varaction2(self))
        return action_list

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
    @type default: L{SpriteGroupRef}, L{Expression} or C{None} (before pre-processing only), depending on the type of result.
    """
    def __init__(self, ranges, default):
        self.ranges = ranges
        self.default = default

    def pre_process(self):
        if isinstance(self.default, expression.Expression):
            self.default = self.default.reduce(global_constants.const_list)
        for r in self.ranges:
            r.pre_process()

    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        self.default.debug_print(indentation + 2)

    def __str__(self):
        ret = ''
        for r in self.ranges:
            ret += '\t%s\n' % str(r)
        if self.default is None:
            ret += '\treturn;\n'
        elif isinstance(self.default, action2.SpriteGroupRef):
            ret += '\t%s;\n' % str(self.default)
        else:
            ret += '\treturn %s;\n' % str(self.default)
        return ret

class RandomSwitch(switch_base_class):
    def __init__(self, param_list, choices, pos):
        if not (3 <= len(param_list) <= 4):
            raise generic.ScriptError("random_switch requires 3 or 4 parameters, encountered %d" % len(param_list), pos)
        #feature
        self.feature = general.parse_feature(param_list[0])

        #type
        self.type = param_list[1]
        # Extract type name and possible argument
        if isinstance(self.type, expression.Identifier):
            self.type_count = None
        elif isinstance(self.type, expression.FunctionCall):
            if len(self.type.params) == 0:
                self.type_count = None
            elif len(self.type.params) == 1:
                self.type_count = self.type.params[0].reduce(global_constants.const_list)
            else:
                raise generic.ScriptError("Value for random_switch parameter 2 'type' can have only one parameter.", self.type.pos)
            self.type = self.type.name
        else:
            raise generic.ScriptError("random_switch parameter 2 'type' should be an identifier, possibly with a parameter.", self.type.pos)

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
        self.switch = None
        self.return_switches = []

    def register_names(self):
        pass

    def add_extra_ret_switch(self, name, expr):
        return_name = expression.Identifier(name, self.pos)
        return_var_range = expression.Identifier('SELF', self.pos)
        # Set result to None, it will be parsed correctly during preprocessing
        return_body = SwitchBody([], None)
        self.return_switches.append(Switch(self.feature, return_var_range, return_name, expr, return_body, self.pos))
        self.return_switches[-1].pre_process()
        return action2.SpriteGroupRef(return_name, [], self.pos)

    def pre_process(self):
        # Make sure, all [in]dependencies refer to existing random switch blocks
        for dep in self.dependent + self.independent:
            spritegroup = action2.resolve_spritegroup(dep.name)
            if not isinstance(spritegroup, RandomSwitch):
                raise generic.ScriptError("Value of (in)dependent '%s' should refer to a random_switch." % dep.name.value, dep.pos)

        if self.type_count is not None and not (isinstance(self.type_count, expression.ConstantNumeric) and 1 <= self.type_count.value <= 15):
            # The 'count' expression is too complex and will need to be stored in grf register 100
            # Create a switch block for this purpose
            va2_feature = self.feature
            va2_range = expression.Identifier('SELF', self.pos)
            va2_name = expression.Identifier(self.name.value, self.pos)

            # Rename ourself
            self.name.value += '@random'

            va2_body = SwitchBody([], action2.SpriteGroupRef(expression.Identifier(self.name.value, self.pos), [], self.pos))
            expr = expression.BinOp(nmlop.STO_TMP, self.type_count, expression.ConstantNumeric(100))
            self.switch = Switch(va2_feature, va2_range, va2_name, expr, va2_body, self.pos)

            self.type_count = expression.ConstantNumeric(0, self.pos) # 0 means 'read from register'

        num_extra_acts = 0
        for choice in self.choices:
            if choice.result is not None and not isinstance(choice.result, (action2.SpriteGroupRef, expression.String)) and not choice.result.supported_by_actionD(False):
                choice.result = self.add_extra_ret_switch('%s@ret%d' % (self.name.value, num_extra_acts), choice.result)
                num_extra_acts += 1

        # Init ourself first
        self.initialize(self.name, self.feature)
        switch_base_class.pre_process(self)
        if self.switch is not None: self.switch.pre_process()

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
        if self.switch is not None:
            print (indentation+2)*' ' + 'Preceding switch block:'
            self.switch.debug_print(indentation + 4)

    def get_action_list(self):
        action_list = []
        if self.prepare_output():
            for ret_switch in self.return_switches:
                action_list.extend(ret_switch.get_action_list())
            action_list += parse_randomswitch(self)
            if self.switch is not None: action_list += self.switch.get_action_list()
        return action_list

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

def parse_randomswitch_type(random_switch):
    """
    Parse the type of a random switch to determine the type and random bits to use.

    @param random_switch: Random switch to parse the type of
    @type random_switch: L{RandomSwitch}

    @return: A tuple containing the following:
                - The type byte of the resulting random action2.
                - The value to use as <count>, None if N/A.
                - The first random bit that should be used (often 0)
                - The number of random bits available
    @rtype: C{tuple} of (C{int}, C{int} or C{None}, C{int}, C{int})
    """
    # Extract some stuff we'll often need
    type_str = random_switch.type.value
    type_pos = random_switch.type.pos
    feature_val = random_switch.feature.value

    # Validate type name / param combination
    if type_str not in random_types:
        raise generic.ScriptError("Unrecognized value for random_switch parameter 2 'type': " + type_str, type_pos)

    if random_switch.type_count is None:
        # No param given
        if random_types[type_str]['param'] == 1:
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' requires a parameter." % type_str, type_pos)
        count = None
    else:
        # Param given
        if random_types[type_str]['param'] == 0:
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' should not have a parameter." % type_str, type_pos)
        if not (0 <= feature_val <= 3):
            raise generic.ScriptError("Value '%s' for random_switch parameter 2 'type' is valid only for vehicles." % type_str, type_pos)
        assert isinstance(random_switch.type_count, expression.ConstantNumeric) and 0 <= random_switch.type_count.value <= 15
        count = random_types[type_str]['value'] | random_switch.type_count.value

    # Determine type byte
    type_byte = random_types[type_str]['type']
    bit_range = random_types[type_str]['range']
    assert (type_byte == 0x84) == (count is not None)

    # Check that feature / type combination is valid
    if feature_val not in num_random_bits:
        raise generic.ScriptError("Invalid feature for random_switch: " + str(feature_val), random_switch.feature.pos)
    if type_byte == 0x83: feature_val = action2var_variables.varact2parent_scope[feature_val]
    if feature_val is None:
        raise generic.ScriptError("Feature '%d' does not have a 'PARENT' scope." % feature_val, type_pos)
    if bit_range != 0 and feature_val not in (0x04, 0x11):
        raise generic.ScriptError("Type 'TILE' is only supported for stations and airport tiles.", type_pos)

    # Determine random bits to use
    bits_available = num_random_bits[feature_val][bit_range]
    start_bit = sum(num_random_bits[feature_val][0:bit_range])
    if bits_available == 0:
        raise generic.ScriptError("No random data is available for the given feature and scope, feature: " + str(feature_val), random_switch.feature.pos)

    return type_byte, count, start_bit, bits_available

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
        if isinstance(choice.result, action2.SpriteGroupRef):
            choice.comment = choice.result.name.value + ';'
        else:
            choice.comment = "return %s;" % str(choice.result)
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
    act2 = spritegroup.get_action2()
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
    type_byte, count, start_bit, bits_available = parse_randomswitch_type(random_switch)

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

    random_action2 = action2random.Action2Random(random_switch.feature.value, random_switch.name.value, type_byte, count, random_switch.triggers.value, randbit, nrand, random_switch.choices)

    action6.free_parameters.save()
    act6 = action6.Action6()
    action_list = []
    offset = 8
    for choice in random_switch.choices:
        choice.result, comment = action2var.parse_result(choice.result, action_list, act6, offset, random_action2, choice.resulting_prob)
        offset += choice.resulting_prob * 2

    for choice in random_switch.choices:
        choice.comment = "(%d/%d) -> (%d/%d): " % (choice.probability.value, total_prob, choice.resulting_prob, nrand) + choice.comment

    if len(act6.modifications) > 0: action_list.append(act6)

    action_list.append(random_action2)
    random_switch.set_action2(random_action2)

    action6.free_parameters.restore()
    return action_list
