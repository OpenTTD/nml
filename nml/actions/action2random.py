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
            if isinstance(choice.result, expression.SpriteGroupRef):
                choice.result = choice.result.get_action2_id()
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


