from nml.actions import action2, action2var_variables
from nml import generic, expression, global_constants

class Action2Random(action2.Action2):
    def __init__(self, feature, name, type_byte, triggers, randbit, nrand, choices):
        action2.Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        self.triggers = triggers
        self.randbit = randbit
        self.nrand = nrand
        self.choices = choices

    def prepare_output(self):
        action2.Action2.prepare_output(self)
        for choice in self.choices:
            if isinstance(choice.result, expression.Identifier):
                choice.result = action2.remove_ref(choice.result.value)
            else:
                choice.result = choice.result.value | 0x8000

    def write(self, file):
        # [80|83] <random-triggers> <randbit> <nrand> <set-ids>
        size = 4 + 2 * self.nrand
        action2.Action2.write(self, file, size)
        file.print_bytex(self.type_byte)
        file.print_bytex(self.triggers)
        file.print_byte(self.randbit)
        file.print_bytex(self.nrand)
        file.newline()

        for choice in self.choices:
            for i in range(0, choice.resulting_prob):
                file.print_wordx(choice.result)
            file.newline()
        file.end_sprite()

class RandomChoice(object):
    def __init__ (self, probability, result):
        if isinstance(probability, expression.Identifier) and probability.value in ('dependent', 'independent'):
            self.probability = probability
        else:
            self.probability = probability.reduce_constant(global_constants.const_list)
            self.resulting_prob = self.probability.value
            if self.probability.value <= 0:
                raise generic.ScriptError("Value for probability should be higher than 0, encountered %d" % self.probability.value, self.probability.pos)
            if result is None:
                raise generic.ScriptError("Returning the computed value is not possible in a random-block, as there is no computed value.", self.probability.pos)
        self.result = result.reduce(global_constants.const_list, False)

    def debug_print(self, indentation):
        print indentation*' ' + 'Probability:'
        self.probability.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.result.debug_print(indentation + 4);
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.probability)
        if isinstance(self.result, expression.Identifier):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
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

def parse_randomblock(random_block):
    feature = random_block.feature.value
    if feature not in num_random_bits:
        raise generic.ScriptError("Invalid feature for random-block: " + str(feature), random_block.feature.pos)
    if random_block.type == 0x83: feature = action2var_variables.varact2parent_scope[feature]
    if feature is None:
        raise generic.ScriptError("Feature '%d' does not have a 'PARENT' scope." % random_block.feature.value, random_block.feature.pos)
    if random_block.bit_range != 0 and feature not in (0x04, 0x11):
        raise generic.ScriptError("Type 'TILE' is only supported for stations and airport tiles.")
    bits_available = num_random_bits[feature][random_block.bit_range]
    start_bit = sum(num_random_bits[feature][0:random_block.bit_range])
    if bits_available == 0:
        raise generic.ScriptError("No random data is available for the given feature and scope, feature: " + str(feature), random_block.feature.pos)

    #determine total probability
    total_prob = 0
    for choice in random_block.choices:
        total_prob += choice.probability.value
        #make reference
        if isinstance(choice.result, expression.Identifier):
            if choice.result.value != 'CB_FAILED':
                action2.add_ref(choice.result.value)
        elif not isinstance(choice.result, expression.ConstantNumeric):
            raise generic.ScriptError("Invalid return value in random-block.", choice.result.pos)
    if len(random_block.choices) == 0:
        raise generic.ScriptError("random-block requires at least one possible choice", random_block.pos)
    assert total_prob > 0

    #How many random bits are needed ?
    nrand = 1
    while nrand < total_prob: nrand <<= 1
    #verify that enough random data is available
    if min(1 << bits_available, 0x80) < nrand:
        raise generic.ScriptError("The maximum sum of all random-block probabilities is %d, encountered %d." % (min(1 << bits_available, 0x80), total_prob), random_block.pos)

    #Dependent random chains
    act2_to_copy = None
    for dep in random_block.dependent:
        if dep.value not in action2.action2_map:
            raise generic.ScriptError("Unknown identifier of random-block: " + dep.value, dep.pos)
        act2 = action2.action2_map[dep.value]
        if not isinstance(act2, Action2Random):
            raise generic.ScriptError("Value for 'dependent' (%s) should refer to another random-block" % dep.value, dep.pos)
        if act2_to_copy is not None:
            if act2_to_copy.randbit != act2.randbit:
                raise generic.ScriptError("Random-block '%s' cannot be dependent on both '%s' and '%s' as these are independent of eachother." %
                    (random_block.name.value, act2_to_copy.name, act2.name), random_block.pos)
            if act2_to_copy.nrand != act2.nrand:
                raise generic.ScriptError("Random-block '%s' cannot be dependent on both '%s' and '%s' as they don't use the same amount of random data." %
                    (random_block.name.value, act2_to_copy.name, act2.name), random_block.pos)
        else:
            act2_to_copy = act2

    if act2_to_copy is not None:
        randbit = act2_to_copy.randbit
        if nrand > act2_to_copy.nrand:
            raise generic.ScriptError("Random-block '%s' cannot be dependent on '%s' as it requires more random data." %
                (random_block.name.value, act2_to_copy.name), random_block.pos)
        nrand = act2_to_copy.nrand
    else:
        randbit = -1

    #INdependent random chains
    possible_mask = ((1 << bits_available) - 1) << start_bit
    for indep in random_block.independent:
        if indep.value not in action2.action2_map:
            raise generic.ScriptError("Unknown identifier of random-block: " + indep.value, indep.pos)
        act2 = action2.action2_map[indep.value]
        if not isinstance(act2, Action2Random):
            raise generic.ScriptError("Value for 'independent' (%s) should refer to another random-block" % indep.value, indep.pos)
        possible_mask &= ~((act2.nrand - 1) << act2.randbit)

    required_mask = nrand - 1
    if randbit != -1:
        #randbit has already been determined. Check that it is suitable
        if possible_mask & (required_mask << randbit) != (required_mask << randbit):
            raise generic.ScriptError("Combination of dependence on and independence from random-blocks is not possible for random-block '%s'." % random_block.name.value, random_block.pos)
    else:
        #find a suitable randbit
        for i in range(start_bit, bits_available + start_bit):
            if possible_mask & (required_mask << i) == (required_mask << i):
                randbit = i
                break
        else:
            raise generic.ScriptError("Independence of all given random-blocks is not possible for random-block '%s'." % random_block.name.value, random_block.pos)

    #divide the 'extra' probabilities in an even manner
    i = 0
    while i < (nrand - total_prob):
        best_choice = None
        best_ratio = 0
        for choice in random_block.choices:
            #float division, so 9 / 10 = 0.9
            ratio = choice.probability.value / float(choice.resulting_prob + 1)
            if ratio > best_ratio:
                best_ratio = ratio
                best_choice = choice
        assert best_choice is not None
        best_choice.resulting_prob += 1
        i += 1

    return [Action2Random(random_block.feature.value, random_block.name.value, random_block.type, random_block.triggers.value, randbit, nrand, random_block.choices)]
