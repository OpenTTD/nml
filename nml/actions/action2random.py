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

from nml import expression, generic, nmlop
from nml.actions import action2, action2real, action2var, action6


class Action2Random(action2.Action2):
    def __init__(self, feature, name, pos, type_byte, count, triggers, randbit, nrand):
        action2.Action2.__init__(self, feature, name, pos)
        self.type_byte = type_byte
        self.count = count
        self.triggers = triggers
        self.randbit = randbit
        self.nrand = nrand
        self.choices = []

    def prepare_output(self, sprite_num):
        action2.Action2.prepare_output(self, sprite_num)
        for choice in self.choices:
            if isinstance(choice.result, expression.SpriteGroupRef):
                choice.result = choice.result.get_action2_id(self.feature)
            else:
                choice.result = choice.result.value | 0x8000

    def write(self, file):
        # <type> [<count>] <random-triggers> <randbit> <nrand> <set-ids>
        size = 4 + 2 * self.nrand + (self.count is not None)
        action2.Action2.write_sprite_start(self, file, size)
        file.print_bytex(self.type_byte)
        if self.count is not None:
            file.print_bytex(self.count)
        file.print_bytex(self.triggers)
        file.print_byte(self.randbit)
        file.print_bytex(self.nrand)
        file.newline()

        for choice in self.choices:
            for _ in range(0, choice.prob):
                file.print_wordx(choice.result)
            file.comment(choice.comment)
        file.end_sprite()


class RandomAction2Choice:
    def __init__(self, result, prob, comment):
        self.result = result
        self.prob = prob
        self.comment = comment


vehicle_random_types = {
    "SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": True},
    "PARENT": {"type": 0x83, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": False},
    "TILE": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": False},
    "BACKWARD_SELF": {"type": 0x84, "param": 1, "first_bit": 0, "num_bits": 8, "triggers": False, "value": 0x00},
    "FORWARD_SELF": {"type": 0x84, "param": 1, "first_bit": 0, "num_bits": 8, "triggers": False, "value": 0x40},
    "BACKWARD_ENGINE": {"type": 0x84, "param": 1, "first_bit": 0, "num_bits": 8, "triggers": False, "value": 0x80},
    "BACKWARD_SAMEID": {"type": 0x84, "param": 1, "first_bit": 0, "num_bits": 8, "triggers": False, "value": 0xC0},
}
random_types = {
    0x00: vehicle_random_types,
    0x01: vehicle_random_types,
    0x02: vehicle_random_types,
    0x03: vehicle_random_types,
    0x04: {
        "SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 16, "triggers": True},
        "TILE": {"type": 0x80, "param": 0, "first_bit": 16, "num_bits": 4, "triggers": True},
    },
    0x05: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": False}},
    0x06: {},
    0x07: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": True}},
    0x08: {},
    0x09: {
        "SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": True},
        "PARENT": {"type": 0x83, "param": 0, "first_bit": 0, "num_bits": 16, "triggers": True},
    },
    0x0A: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 16, "triggers": False}},
    0x0B: {},
    0x0C: {},
    0x0D: {},
    0x0E: {},
    0x0F: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 8, "triggers": False}},
    0x10: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 2, "triggers": False}},
    0x11: {
        "SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 16, "triggers": False},
        "TILE": {"type": 0x80, "param": 0, "first_bit": 16, "num_bits": 4, "triggers": False},
    },
    0x12: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 2, "triggers": False}},
    0x13: {"SELF": {"type": 0x80, "param": 0, "first_bit": 0, "num_bits": 2, "triggers": False}},
}


def parse_randomswitch_type(random_switch):
    """
    Parse the type of a random switch to determine the type and random bits to use.

    @param random_switch: Random switch to parse the type of
    @type random_switch: L{RandomSwitch}

    @return: A tuple containing the following:
                - The type byte of the resulting random action2.
                - The value to use as <count>, None if N/A.
                - Expression to parse in a preceding switch-block, None if N/A.
                - The first random bit that should be used (often 0)
                - The number of random bits available
    @rtype: C{tuple} of (C{int}, C{int} or C{None}, L{Expression} or C{None}, C{int}, C{int})
    """
    # Extract some stuff we'll often need
    type_str = random_switch.type.value
    type_pos = random_switch.type.pos
    feature_val = next(iter(random_switch.feature_set))

    # Validate type name / param combination
    if type_str not in random_types[feature_val]:
        raise generic.ScriptError(
            "Invalid combination for random_switch feature {:d} and type '{}'. ".format(feature_val, type_str), type_pos
        )
    type_info = random_types[feature_val][type_str]

    count_expr = None
    if random_switch.type_count is None:
        # No param given
        if type_info["param"] == 1:
            raise generic.ScriptError(
                "Value '{}' for random_switch parameter 2 'type' requires a parameter.".format(type_str), type_pos
            )
        count = None
    else:
        # Param given
        if type_info["param"] == 0:
            raise generic.ScriptError(
                "Value '{}' for random_switch parameter 2 'type' should not have a parameter.".format(type_str),
                type_pos,
            )
        if (
            isinstance(random_switch.type_count, expression.ConstantNumeric)
            and 1 <= random_switch.type_count.value <= 15
        ):
            count = random_switch.type_count.value
        else:
            count = 0
            count_expr = nmlop.STO_TMP(random_switch.type_count, 0x100, type_pos)
        count = type_info["value"] | count

    if random_switch.triggers.value != 0 and not type_info["triggers"]:
        raise generic.ScriptError(
            "Triggers may not be set for random_switch feature {:d} and type '{}'. ".format(feature_val, type_str),
            type_pos,
        )

    # Determine type byte and random bits
    type_byte = type_info["type"]
    start_bit = type_info["first_bit"]
    bits_available = type_info["num_bits"]

    return type_byte, count, count_expr, start_bit, bits_available


def lookup_random_action2(sg_ref):
    """
    Lookup a sprite group reference to find the corresponding random action2

    @param sg_ref: Reference to random action2
    @type sg_ref: L{SpriteGroupRef}

    @return: Random action2 corresponding to this sprite group, or None if N/A
    @rtype: L{Action2Random} or C{None}
    """
    spritegroup = action2.resolve_spritegroup(sg_ref.name)
    act2 = spritegroup.random_act2
    assert act2 is None or isinstance(act2, Action2Random)
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
    # Dependent random chains
    act2_to_copy = None
    for dep in random_switch.dependent:
        act2 = lookup_random_action2(dep)
        if act2 is None:
            continue  # May happen if said random switch is not used and therefore not parsed
        if act2_to_copy is not None:
            if act2_to_copy.randbit != act2.randbit:
                msg = (
                    "random_switch '{}' cannot be dependent on both '{}' and '{}'"
                    " as these are independent of each other."
                ).format(random_switch.name.value, act2_to_copy.name, act2.name)
                raise generic.ScriptError(msg, random_switch.pos)

            if act2_to_copy.nrand != act2.nrand:
                msg = (
                    "random_switch '{}' cannot be dependent on both '{}' and '{}'"
                    " as they don't use the same amount of random data."
                ).format(random_switch.name.value, act2_to_copy.name, act2.name)
                raise generic.ScriptError(msg, random_switch.pos)
        else:
            act2_to_copy = act2

    if act2_to_copy is not None:
        randbit = act2_to_copy.randbit
        if nrand > act2_to_copy.nrand:
            msg = "random_switch '{}' cannot be dependent on '{}' as it requires more random data."
            msg = msg.format(random_switch.name.value, act2_to_copy.name)
            raise generic.ScriptError(msg, random_switch.pos)

        nrand = act2_to_copy.nrand
    else:
        randbit = -1

    # INdependent random chains
    possible_mask = ((1 << bits_available) - 1) << start_bit
    for indep in random_switch.independent:
        act2 = lookup_random_action2(indep)
        if act2 is None:
            continue  # May happen if said random switch is not used and therefore not parsed
        possible_mask &= ~((act2.nrand - 1) << act2.randbit)

    required_mask = nrand - 1
    if randbit != -1:
        # randbit has already been determined. Check that it is suitable
        if possible_mask & (required_mask << randbit) != (required_mask << randbit):
            msg = (
                "Combination of dependence on and independence from"
                " random_switches is not possible for random_switch '{}'."
            ).format(random_switch.name.value)
            raise generic.ScriptError(msg, random_switch.pos)
    else:
        # find a suitable randbit
        for i in range(start_bit, bits_available + start_bit):
            if possible_mask & (required_mask << i) == (required_mask << i):
                randbit = i
                break
        else:
            msg = "Independence of all given random_switches is not possible for random_switch '{}'."
            msg = msg.format(random_switch.name.value)
            raise generic.ScriptError(msg, random_switch.pos)

    return randbit, nrand


def parse_randomswitch(random_switch):
    """
    Parse a randomswitch block into actions

    @param random_switch: RandomSwitch block to parse
    @type random_switch: L{RandomSwitch}

    @return: List of actions
    @rtype: C{list} of L{BaseAction}
    """
    action_list = action2real.create_spriteset_actions(random_switch)
    feature = next(iter(random_switch.feature_set))
    type_byte, count, count_expr, start_bit, bits_available = parse_randomswitch_type(random_switch)

    total_prob = sum(choice.probability.value for choice in random_switch.choices)
    assert total_prob > 0
    nrand = 1
    while nrand < total_prob:
        nrand <<= 1

    # Verify that enough random data is available
    if min(1 << bits_available, 0x80) < nrand:
        msg = "The maximum sum of all random_switch probabilities is {:d}, encountered {:d}."
        msg = msg.format(min(1 << bits_available, 0x80), total_prob)
        raise generic.ScriptError(msg, random_switch.pos)

    randbit, nrand = parse_randomswitch_dependencies(random_switch, start_bit, bits_available, nrand)

    random_action2 = Action2Random(
        feature,
        random_switch.name.value,
        random_switch.pos,
        type_byte,
        count,
        random_switch.triggers.value,
        randbit,
        nrand,
    )
    random_switch.random_act2 = random_action2

    action6.free_parameters.save()
    act6 = action6.Action6()
    offset = 8 if count is not None else 7

    # divide the 'extra' probabilities in an even manner
    i = 0
    resulting_prob = {c: c.probability.value for c in random_switch.choices}
    while i < (nrand - total_prob):
        best_choice = None
        best_ratio = 0
        for choice in random_switch.choices:
            # float division, so 9 / 10 = 0.9
            ratio = choice.probability.value / float(resulting_prob[choice] + 1)
            if ratio > best_ratio:
                best_ratio = ratio
                best_choice = choice
        assert best_choice is not None
        resulting_prob[best_choice] += 1
        i += 1

    for choice in random_switch.choices:
        res_prob = resulting_prob[choice]
        result, comment = action2var.parse_result(
            choice.result.value,
            action_list,
            act6,
            offset,
            random_action2,
            None,
            0x8A if type_byte == 0x83 else 0x89,
            res_prob,
        )
        offset += res_prob * 2
        comment = "({:d}/{:d}) -> ({:d}/{:d}): ".format(choice.probability.value, total_prob, res_prob, nrand) + comment
        random_action2.choices.append(RandomAction2Choice(result, res_prob, comment))

    if len(act6.modifications) > 0:
        action_list.append(act6)

    action_list.append(random_action2)
    if count_expr is None:
        random_switch.set_action2(random_action2, feature)
    else:
        # Create intermediate varaction2 to compute parameter for type 0x84
        varaction2 = action2var.Action2Var(
            feature, "{}@registers".format(random_switch.name.value), random_switch.pos, 0x89
        )
        varact2parser = action2var.Varaction2Parser(feature)
        varact2parser.parse_expr(count_expr)
        varaction2.var_list = varact2parser.var_list
        action_list.extend(varact2parser.extra_actions)
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
        if len(extra_act6.modifications) > 0:
            action_list.append(extra_act6)
        ref = expression.SpriteGroupRef(random_switch.name, [], None, random_action2)
        varaction2.ranges.append(
            action2var.VarAction2Range(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, "")
        )
        varaction2.default_result = ref
        varaction2.default_comment = ""

        # Add two references (default + range)
        action2.add_ref(ref, varaction2)
        action2.add_ref(ref, varaction2)
        random_switch.set_action2(varaction2, feature)
        action_list.append(varaction2)

    action6.free_parameters.restore()
    return action_list
