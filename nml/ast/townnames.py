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

import heapq

from nml import expression, generic, grfstrings
from nml.actions import actionF
from nml.ast import base_statement

townname_serial = 1


class TownNames(base_statement.BaseStatement):
    """
    'town_names' ast node.

    @ivar name: Name ID of the town_name.
    @type name: C{None}, L{Identifier}, or L{ConstantNumeric}

    @ivar id_number: Allocated ID number for this town_name action F node.
    @type id_number: C{None} or C{int}

    @ivar style_name: Name of the translated string containing the name of the style, if any.
    @type style_name: C{None} or L{String}

    @ivar actFs: Action F instance needed before this one.
    @type actFs: C{list} of L{ActionF}

    @ivar parts: Parts of the names.
    @type parts: C{list} of L{TownNamesPart}

    @ivar param_list: Stored parameter list.
    @type param_list: C{list} of (L{TownNamesPart} or L{TownNamesParam})
    """

    def __init__(self, name, param_list, pos):
        base_statement.BaseStatement.__init__(self, "town_names-block", pos, False, False)
        self.name = name
        self.param_list = param_list

        self.id_number = None
        self.style_name = None
        self.actFs = []
        self.parts = []

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Town name")
        if self.name is not None:
            generic.print_dbg(indentation + 2, "Name:")
            self.name.debug_print(indentation + 4)
        for param in self.param_list:
            param.debug_print(indentation + 2)

    def pre_process(self):
        self.actFs = []
        self.parts = []
        for param in self.param_list:
            if isinstance(param, TownNamesPart):
                actFs, part = param.make_actions()
                self.actFs.extend(actFs)
                self.parts.append(part)
            else:
                if param.key.value != "styles":
                    raise generic.ScriptError("Expected 'styles' keyword.", param.pos)
                if len(param.value.params) > 0:
                    raise generic.ScriptError("Parameters of the 'styles' were not expected.", param.pos)
                if self.style_name is not None:
                    raise generic.ScriptError("'styles' is already defined.", self.pos)
                self.style_name = param.value

        if len(self.parts) == 0:
            raise generic.ScriptError("Missing name parts in a town_names item.", self.pos)

        # 'name' is actually a number.
        # Allocate it now, before the self.prepare_output() call (to prevent names to grab it).
        if self.name is not None and not isinstance(self.name, expression.Identifier):
            value = self.name.reduce_constant()
            if not isinstance(value, expression.ConstantNumeric):
                raise generic.ScriptError("ID should be an integer number.", self.pos)

            self.id_number = value.value
            if self.id_number < 0 or self.id_number > 0x7F:
                raise generic.ScriptError("ID must be a number between 0 and 0x7f (inclusive)", self.pos)

            if self.id_number not in actionF.free_numbers:
                raise generic.ScriptError("town names ID 0x{:x} is already used.".format(self.id_number), self.pos)
            actionF.free_numbers.remove(self.id_number)

    def __str__(self):
        ret = "town_names"
        if self.name is not None:
            ret += "({})".format(self.name)
        ret += "{{\n{}}}\n".format("".join(str(x) for x in self.param_list))
        return ret

    def get_action_list(self):
        return self.actFs + [actionF.ActionF(self.name, self.id_number, self.style_name, self.parts, self.pos)]


class TownNamesPart:
    """
    A class containing a town name part.

    @ivar pieces: Pieces of the town name part.
    @type pieces: C{list} of (L{TownNamesEntryDefinition} or L{TownNamesEntryText})

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}

    @ivar startbit: First bit to use for this part, if defined.
    @type startbit: C{int} or C{None}

    @ivar num_bits: Number of bits to use, if defined.
    @type num_bits: C{int} or C{None}
    """

    def __init__(self, pieces, pos):
        self.pos = pos
        self.pieces = pieces

        self.startbit = None
        self.num_bits = None

    def make_actions(self):
        """
        Construct new actionF instances to store all pieces of this part, if needed.

        @return: Action F that should be defined before, and the processed part.
        @rtype: C{list} of L{ActionF}, L{TownNamesPart}
        """
        new_pieces = []
        for piece in self.pieces:
            piece.pre_process()
            if piece.probability.value == 0:
                generic.print_warning(
                    generic.Warning.OPTIMISATION, "Dropping town name piece with 0 probability.", piece.pos
                )
            else:
                new_pieces.append(piece)

        self.pieces = new_pieces

        actFs = self.move_pieces()
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected names and/or town_name references in the part.", self.pos)
        if len(self.pieces) > 255:
            raise generic.ScriptError(
                "Too many values in a part, found {:d}, maximum is 255".format(len(self.pieces)), self.pos
            )

        return actFs, self

    def move_pieces(self):
        """
        Move pieces to new action F instances to make it fit, if needed.

        @return: Created action F instances.
        @rtype:  C{list} of L{ActionF}

        @note: Function may change L{pieces}.
        """
        global townname_serial

        if len(self.pieces) <= 255:
            return []  # Trivially correct.

        # There are too many pieces.
        number_action_f = (len(self.pieces) + 254) // 255
        pow2 = 1
        while pow2 < number_action_f:
            pow2 = pow2 * 2
        if pow2 < 255:
            number_action_f = pow2

        heap = []  # Heap of (summed probability, subset-of-pieces)
        i = 0
        while i < number_action_f:
            # Index 'i' is added to have a unique sorting when lists have equal total probabilities.
            heapq.heappush(heap, (0, i, []))
            i = i + 1

        finished_actions = []
        # Index 'idx' is added to have a unique sorting when pieces have equal probabilities.
        rev_pieces = sorted(((p.probability.value, idx, p) for idx, p in enumerate(self.pieces)), reverse=True)
        for prob, _idx, piece in rev_pieces:
            while True:
                sub = heapq.heappop(heap)
                if len(sub[2]) < 255:
                    break
                # If a subset already has the max number of parts, consider it finished.
                finished_actions.append(sub)

            sub[2].append(piece)
            sub = (sub[0] + prob, sub[1], sub[2])
            heapq.heappush(heap, sub)

        finished_actions.extend(heap)

        # To ensure the chances do not get messed up due to one part needing less bits for its
        # selection, all parts are forced to use the same number of bits.
        max_prob = max(sub[0] for sub in finished_actions)
        num_bits = 1
        while (1 << num_bits) < max_prob:
            num_bits = num_bits + 1

        # Assign to action F
        actFs = []
        for _prob, _idx, sub in finished_actions:
            actF_name = expression.Identifier("**townname #{:d}**".format(townname_serial), None)
            townname_serial = townname_serial + 1
            town_part = TownNamesPart(sub, self.pos)
            town_part.set_numbits(num_bits)
            actF = actionF.ActionF(actF_name, None, None, [town_part], self.pos)
            actFs.append(actF)

            # Remove pieces of 'sub' from self.pieces
            counts = len(self.pieces), len(sub)
            sub_set = set(sub)
            self.pieces = [piece for piece in self.pieces if piece not in sub_set]
            assert len(self.pieces) == counts[0] - counts[1]

            self.pieces.append(TownNamesEntryDefinition(actF_name, expression.ConstantNumeric(1), self.pos))

        # update self.parts
        return actFs

    def assign_bits(self, startbit):
        """
        Assign bits for this piece.

        @param startbit: First bit free for use.
        @type  startbit: C{int}

        @return: Number of bits needed for this piece.
        @rtype:  C{int}
        """
        assert len(self.pieces) <= 255
        total = sum(piece.probability.value for piece in self.pieces)

        if self.startbit is None or self.startbit < startbit:
            self.startbit = startbit
        if self.num_bits is None:
            n = 1
            while total > (1 << n):
                n = n + 1
            self.num_bits = n
        assert (1 << self.num_bits) >= total
        return self.num_bits

    def set_numbits(self, numbits):
        """
        Set the number of bits that this part should use.
        """
        assert self.num_bits is None
        self.num_bits = numbits

    def debug_print(self, indentation):
        total = sum(piece.probability.value for piece in self.pieces)
        generic.print_dbg(indentation, "Town names part (total {:d})".format(total))
        for piece in self.pieces:
            piece.debug_print(indentation + 2, total)

    def __str__(self):
        return "{{\n\t{}\n}}\n".format("\n\t".join(str(piece) for piece in self.pieces))

    def get_length(self):
        size = 3  # textcount, firstbit, bitcount bytes.
        size += sum(piece.get_length() for piece in self.pieces)
        return size

    def resolve_townname_id(self):
        """
        Resolve the reference numbers to previous C{town_names} blocks.

        @return: Set of referenced C{town_names} block numbers.
        """
        blocks = set()
        for piece in self.pieces:
            block = piece.resolve_townname_id()
            if block is not None:
                blocks.add(block)
        return blocks

    def write(self, file):
        file.print_bytex(len(self.pieces))
        file.print_bytex(self.startbit)
        file.print_bytex(self.num_bits)
        for piece in self.pieces:
            piece.write(file)
            file.newline()


class TownNamesParam:
    """
    Class containing a parameter of a town name.
    Currently known key/values:
     - 'styles'  / string expression
    """

    def __init__(self, key, value, pos):
        self.key = key
        self.value = value
        self.pos = pos

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Town names param")
        generic.print_dbg(indentation + 2, "Key:")
        self.key.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Value:")
        self.value.debug_print(indentation + 4)

    def __str__(self):
        return "{}: {};\n".format(self.key, self.value)


class TownNamesEntryDefinition:
    """
    An entry in a part referring to a non-final town name, with a given probability.

    @ivar def_number: Name or number referring to a previous town_names node.
    @type def_number: L{Identifier} or L{ConstantNumeric}

    @ivar number: Actual ID to use.
    @type number: C{None} or C{int}

    @ivar probability: Probability of picking this reference.
    @type probability: C{ConstantNumeric}

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}
    """

    def __init__(self, def_number, probability, pos):
        self.def_number = def_number
        self.number = None
        self.probability = probability
        self.pos = pos

    def pre_process(self):
        self.number = None
        if not isinstance(self.def_number, expression.Identifier):
            self.def_number = self.def_number.reduce_constant()
            if not isinstance(self.def_number, expression.ConstantNumeric):
                raise generic.ScriptError("Reference to other town name ID should be an integer number.", self.pos)
            if self.def_number.value < 0 or self.def_number.value > 0x7F:
                raise generic.ScriptError(
                    "Reference number out of range (must be between 0 and 0x7f inclusive).", self.pos
                )

        self.probability = self.probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7F:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        if isinstance(self.def_number, expression.Identifier):
            name_text = "name '" + self.def_number.value + "'"
        else:
            name_text = "number 0x{:x}".format(self.def_number.value)

        generic.print_dbg(
            indentation,
            "Insert town_name ID {} with probability {:d}/{:d}".format(name_text, self.probability.value, total),
        )

    def __str__(self):
        return "town_names({}, {:d}),".format(str(self.def_number), self.probability.value)

    def get_length(self):
        return 2

    def resolve_townname_id(self):
        """
        Resolve the reference number to a previous C{town_names} block.

        @return: Number of the referenced C{town_names} block.
        """
        if isinstance(self.def_number, expression.Identifier):
            self.number = actionF.named_numbers.get(self.def_number.value)
            if self.number is None:
                raise generic.ScriptError(
                    'Town names name "{}" is not defined or points to a next town_names node'.format(
                        self.def_number.value
                    ),
                    self.pos,
                )
        else:
            self.number = self.def_number.value
            if self.number not in actionF.numbered_numbers:
                raise generic.ScriptError(
                    'Town names number "{}" is not defined or points to a next town_names node'.format(self.number),
                    self.pos,
                )
        return self.number

    def write(self, file):
        file.print_bytex(self.probability.value | 0x80)
        file.print_bytex(self.number)


class TownNamesEntryText:
    """
    An entry in a part, a text-string with a given probability.

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}
    """

    def __init__(self, id, text, probability, pos):
        self.id = id
        self.text = text
        self.probability = probability
        self.pos = pos

    def pre_process(self):
        if self.id.value != "text":
            raise generic.ScriptError("Expected 'text' prefix.", self.pos)

        if not isinstance(self.text, expression.StringLiteral):
            raise generic.ScriptError("Expected string literal for the name.", self.pos)

        self.probability = self.probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7F:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        generic.print_dbg(
            indentation, "Text {} with probability {:d}/{:d}".format(self.text.value, self.probability.value, total)
        )

    def __str__(self):
        return "text({}, {:d}),".format(self.text, self.probability.value)

    def get_length(self):
        return 1 + grfstrings.get_string_size(self.text.value)  # probability, text

    def resolve_townname_id(self):
        """
        Resolve the reference number to a previous C{town_names} block.

        @return: C{None}, as being the block number of a referenced previous C{town_names} block.
        """
        return None

    def write(self, file):
        file.print_bytex(self.probability.value)
        file.print_string(self.text.value, final_zero=True)
