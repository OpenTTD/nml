from nml import expression, generic, grfstrings
from nml.actions import actionF


class TownNames(object):
    """
    town_names ast node.

    @ivar name: Name ID of the town_name.
    @type name: C{None}, L{Identifier}, or L{ConstantNumeric}

    @ivar id_number: Allocated ID number for this town_name action F node.
    @type id_number: C{None} or C{int}

    @ivar style_name: Name of the translated string containing the name of the style, if any.
    @type style_name: C{None} or L{String}

    @ivar style_names: List translations of L{style_name}, pairs (languageID, text).
    @type style_names: C{list} of (C{int}, L{Identifier})

    @ivar parts: Parts of the names.
    @type parts: C{list} of L{TownNamesPart}

    @ivar free_bit: First available bit above the bits used by this block.
    @type free_bit: C{None} if unset, else C{int}

    @ivar pos: Position information of the 'town_names' block.
    @type pos: L{Position}

    @ivar param_list: Stored parameter list.
    @type param_list: C{list} of (L{TownNamesPart} or L{TownNamesParam})
    """
    def __init__(self, name, param_list, pos):
        self.name = name
        self.param_list = param_list
        self.pos = pos

        self.id_number = None
        self.style_name = None
        self.style_names = []
        self.parts = []
        self.free_bit = None

    def pre_process(self):
        for param in self.param_list:
            param.pre_process()

            if isinstance(param, TownNamesPart): self.parts.append(param)
            else:
                if param.key.value != 'styles':
                    raise generic.ScriptError("Expected 'styles' keyword.", param.pos)
                if len(param.value.params) > 0:
                    raise generic.ScriptError("Parameters of the 'styles' were not expected.", param.pos)
                if self.style_name is not None:
                    raise generic.ScriptError("'styles' is already defined.", self.pos)
                self.style_name = param.value.name

        if len(self.parts) == 0:
            raise generic.ScriptError("Missing name parts in a town_names item.", self.pos)

        # 'name' is actually a number.
        # Allocate it now, before the self.prepare_output() call (to prevent names to grab it).
        if self.name is not None and not isinstance(self.name, expression.Identifier):
            value = self.name.reduce_constant()
            if not isinstance(value, expression.ConstantNumeric):
                raise generic.ScriptError("ID should be an integer number.", self.pos)

            self.id_number = value.value
            if self.id_number < 0 or self.id_number > 0x7f:
                raise generic.ScriptError("ID must be a number between 0 and 0x7f (inclusive)", self.pos)

            if self.id_number not in actionF.free_numbers:
                raise generic.ScriptError("town names ID 0x%x is already used." % self.id_number, self.pos)
            actionF.free_numbers.remove(self.id_number)

    def prepare_output(self):
        # Resolve references to earlier townname actions
        blocks = set()
        for part in self.parts:
            blocks.update(part.resolve_townname_id())

        # Allocate a number for this action F.
        if self.name is None or isinstance(self.name, expression.Identifier):
            self.id_number = actionF.get_free_id()
            if isinstance(self.name, expression.Identifier):
                if self.name.value in actionF.named_numbers:
                    raise generic.ScriptError('Cannot define town name "%s", it is already in use' % self.name, self.pos)
                actionF.named_numbers[self.name.value] = self.id_number # Add name to the set 'safe' names.
        else: actionF.numbered_numbers.add(self.id_number) # Add number to the set of 'safe' numbers.

        actionF.town_names_blocks[self.id_number] = self # Add self to the available blocks.

        # Ask descendants for the lowest available bit.
        if len(blocks) == 0: startbit = 0 # No descendants, all bits are free.
        else: startbit = max(actionF.town_names_blocks[block].free_bit for block in blocks)
        # Allocate random bits to all parts.
        for part in self.parts:
            num_bits = part.assign_bits(startbit)
            startbit += num_bits
        self.free_bit = startbit

        if startbit > 32:
            raise generic.ScriptError("Not enough random bits for the town name generation (%d needed, 32 available)" % startbit, self.pos)

        # Pull style names if needed.
        if self.style_name is not None:
            if self.style_name.value not in grfstrings.grf_strings:
                raise generic.ScriptError("Unknown string: " + self.style_name.value, self.style_name.pos)
            self.style_names = [(transl['lang'], transl['text']) for transl in grfstrings.grf_strings[self.style_name.value]]
            self.style_names.sort()
            if len(self.style_names) == 0:
                raise generic.ScriptError('Style "%s" defined, but no translations found for it' % self.style_name.value, self.pos)
        else: self.style_names = []


    def get_id(self):
        return self.id_number | (0x80 if len(self.style_names) > 0 else 0)

    # Style names
    def get_length_styles(self):
        if len(self.style_names) == 0: return 0
        size = 0
        for _lang, txt in self.style_names:
            size += 1 + grfstrings.get_string_size(txt) # Language ID, text
        return size + 1 # Terminating 0

    def write_styles(self, file):
        if len(self.style_names) == 0: return

        for lang, txt in self.style_names:
            file.print_bytex(lang)
            file.print_string(txt, final_zero = True)
        file.print_bytex(0)

    # Parts
    def get_length_parts(self):
        size = 1 # num_parts byte
        return size + sum(part.get_length() for part in self.parts)

    def write_parts(self, file):
        file.print_bytex(len(self.parts))
        for part in self.parts:
            part.write(file)
            file.newline()


    def debug_print(self, indentation):
        if isinstance(self.name, basestring):
            name_text = "name = " + repr(self.name)
            if self.id_number is not None: name_text += " (allocated number is 0x%x)" % self.id_number
        elif self.id_number is not None:
            name_text = "number = 0x%x" % self.id_number
        else:
            name_text = "(unnamed)"

        print indentation*' ' + 'Town name ' + name_text
        if self.style_name is not None:
            print indentation*' ' + "  style name string:", self.style_name.value
        for part in self.parts:
            print indentation*' ' + "-name part:"
            part.debug_print(indentation + 2)

    def get_action_list(self):
        return [actionF.ActionF(self)]


class TownNamesPart(object):
    """
    A class containing a town name part.

    @ivar pieces: Pieces of the town name part.
    @type pieces: C{list} of (L{TownNamesEntryDefinition} or L{TownNamesEntryText})

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}

    @ivar total: Sum of probabilities.
    @type total: C{int}

    @ivar startbit: First bit to use for this part, if defined.
    @type startbit: C{int} or C{None}

    @ivar num_bits: Number of bits to use.
    @type num_bits: C{int}
    """
    def __init__(self, pieces, pos):
        self.pos = pos
        self.pieces = pieces

        self.total = 0
        self.startbit = None
        self.num_bits = 0

    def pre_process(self):
        for piece in self.pieces:
            piece.pre_process()

        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected names and/or town_name references in the part.", self.pos)

        self.total = sum(piece.probability.value for piece in self.pieces)

    def assign_bits(self, startbit):
        """
        Assign bits for this piece.

        @param startbit: First bit free for use.
        @type  startbit: C{int}

        @return: Number of bits needed for this piece.
        @rtype:  C{int}
        """
        self.startbit = startbit
        n = 1
        while self.total > (1 << n): n = n + 1
        self.num_bits = n
        return n

    def debug_print(self, indentation):
        print indentation*' ' + 'Town names part (total %d)' % self.total
        for piece in self.pieces:
            piece.debug_print(indentation + 2, self.total)

    def get_length(self):
        size = 3 # textcount, firstbit, bitcount bytes.
        size += sum(piece.get_length() for piece in self.pieces)
        return size

    def resolve_townname_id(self):
        '''
        Resolve the reference numbers to previous C{town_names} blocks.

        @return: Set of referenced C{town_names} block numbers.
        '''
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected at least one value in a part.", self.pos)
        if len(self.pieces) > 255:
            raise generic.ScriptError("Too many values in a part, found %d, maximum is 255" % len(self.pieces), self.pos)
        blocks = set()
        for piece in self.pieces:
            block = piece.resolve_townname_id()
            if block is not None: blocks.add(block)
        return blocks

    def write(self, file):
        file.print_bytex(len(self.pieces))
        file.print_bytex(self.startbit)
        file.print_bytex(self.num_bits)
        for piece in self.pieces:
            piece.write(file)


class TownNamesParam(object):
    """
    Class containing a parameter of a town name.
    Currently known key/values:
     - 'styles'  / string expression
    """
    def __init__(self, key, value, pos):
        self.key = key
        self.value = value
        self.pos = pos

    def pre_process(self):
        pass


class TownNamesEntryDefinition(object):
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
        self.probability = probability
        self.pos = pos

    def pre_process(self):
        self.number = None
        if not isinstance(self.def_number, expression.Identifier):
            self.def_number = self.def_number.reduce_constant()
            if not isinstance(self.def_number, expression.ConstantNumeric):
                raise generic.ScriptError("Reference to other town name ID should be an integer number.", self.pos)
            if self.def_number.value < 0 or self.def_number.value > 0x7f:
                raise generic.ScriptError("Reference number out of range (must be between 0 and 0x7f inclusive).", self.pos)

        self.probability = self.probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        if isinstance(self.def_number, expression.Identifier): name_text = "name '" + self.def_number.value + "'"
        else: name_text = "number 0x%x" % self.def_number.value
        print indentation*' ' + ('Insert town_name ID %s with probability %d/%d' % (name_text, self.probability.value, total))

    def get_length(self):
        return 2

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: Number of the referenced C{town_names} block.
        '''
        if isinstance(self.def_number, expression.Identifier):
            self.number = actionF.named_numbers.get(self.def_number.value)
            if self.number is None:
                raise generic.ScriptError('Town names name "%s" is not defined or points to a next town_names node' % self.def_number.value, self.pos)
        else:
            self.number = self.def_number.value
            if self.number not in actionF.numbered_numbers:
                raise generic.ScriptError('Town names number "%s" is not defined or points to a next town_names node' % self.number, self.pos)
        return self.number

    def write(self, file):
        file.print_bytex(self.probability.value | 0x80)
        file.print_bytex(self.number)

class TownNamesEntryText(object):
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
        if self.id.value != 'text':
            raise generic.ScriptError("Expected 'text' prefix.", self.pos)

        if not isinstance(self.text, expression.StringLiteral):
            raise generic.ScriptError("Expected string literal for the name.", self.pos)

        self.probability = self.probability.reduce_constant()
        if not isinstance(self.probability, expression.ConstantNumeric):
            raise generic.ScriptError("Probability should be an integer number.", self.pos)
        if self.probability.value < 0 or self.probability.value > 0x7f:
            raise generic.ScriptError("Probability out of range (must be between 0 and 0x7f inclusive).", self.pos)

    def debug_print(self, indentation, total):
        print indentation*' ' + ('Text %s with probability %d/%d' % (self.text.value, self.probability.value, total))

    def get_length(self):
        return 1 + grfstrings.get_string_size(self.text.value) # probability, text

    def resolve_townname_id(self):
        '''
        Resolve the reference number to a previous C{town_names} block.

        @return: C{None}, as being the block number of a referenced previous C{town_names} block.
        '''
        return None

    def write(self, file):
        file.print_bytex(self.probability.value)
        file.print_string(self.text.value, final_zero = True)
