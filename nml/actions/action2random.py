from nml.actions import action2
from nml import generic, expression, global_constants

class Action2Random(action2.Action2):
    def __init__(self, feature, name, type_byte, count, triggers, randbit, nrand, choices):
        action2.Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        self.count = count
        self.triggers = triggers
        self.randbit = randbit
        self.nrand = nrand
        self.choices = choices

    def prepare_output(self):
        action2.Action2.prepare_output(self)
        for choice in self.choices:
            if isinstance(choice.result, action2.SpriteGroupRef):
                choice.result = action2.remove_ref(choice.result)
            else:
                choice.result = choice.result.value | 0x8000

    def write(self, file):
        # <type> [<count>] <random-triggers> <randbit> <nrand> <set-ids>
        size = 4 + 2 * self.nrand + (self.count is not None)
        action2.Action2.write_sprite_start(self, file, size)
        file.print_bytex(self.type_byte)
        if self.count is not None: file.print_bytex(self.count)
        file.print_bytex(self.triggers)
        file.print_byte(self.randbit)
        file.print_bytex(self.nrand)
        file.newline()

        for choice in self.choices:
            for i in range(0, choice.resulting_prob):
                file.print_wordx(choice.result)
            file.comment(choice.comment)
        file.end_sprite()

class RandomChoice(object):
    """
    Class to hold one of the possible choices in a random_switch

    @ivar probability: Relative chance for this choice to be chosen
    @type probability: L{Expression}

    @ivar result: Result of this choice, either another action2 or a return value
    @type result: L{SpriteGroupRef} or L{Expression}

    @ivar resulting_prob: Resulting probability for this choice, may be altered during action generation
    @type resulting_prob: C{int}

    @ivar comment: Comment string to be appended to this choice
    @type comment: C{str}
    """
    def __init__ (self, probability, result):
        if isinstance(probability, expression.Identifier) and probability.value in ('dependent', 'independent'):
            self.probability = probability
        else:
            self.probability = probability.reduce_constant(global_constants.const_list)
            self.resulting_prob = self.probability.value
            if self.probability.value <= 0:
                raise generic.ScriptError("Value for probability should be higher than 0, encountered %d" % self.probability.value, self.probability.pos)
            if result is None:
                raise generic.ScriptError("Returning the computed value is not possible in a random_switch, as there is no computed value.", self.probability.pos)
        if isinstance(result, action2.SpriteGroupRef):
            self.result = result
        else:
            self.result = result.reduce(global_constants.const_list)

    def debug_print(self, indentation):
        print indentation*' ' + 'Probability:'
        self.probability.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.probability)
        if isinstance(self.result, action2.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret
