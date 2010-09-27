import heapq
from nml import expression, generic, grfstrings
from nml.actions import actionF

townname_serial = 1

class TownNames(object):
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
        self.actFs = []
        self.parts = []

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

    def pre_process(self):
        self.actFs = []
        self.parts = []
        for param in self.param_list:
            if isinstance(param, TownNamesPart):
                actFs, part = param.make_actions()
                self.actFs.extend(actFs)
                self.parts.append(part)
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


    def get_action_list(self):
        return self.actFs + [actionF.ActionF(self.name, self.id_number, self.style_name, self.parts, self.pos)]


class TownNamesPart(object):
    """
    A class containing a town name part.

    @ivar pieces: Pieces of the town name part.
    @type pieces: C{list} of (L{TownNamesEntryDefinition} or L{TownNamesEntryText})

    @ivar pos: Position information of the parts block.
    @type pos: L{Position}

    @ivar startbit: First bit to use for this part, if defined.
    @type startbit: C{int} or C{None}

    @ivar num_bits: Number of bits to use.
    @type num_bits: C{int}
    """
    def __init__(self, pieces, pos):
        self.pos = pos
        self.pieces = pieces

        self.startbit = None
        self.num_bits = 0

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
                generic.print_warning("Dropping town name piece with 0 probability.", piece.pos)
            else:
                new_pieces.append(piece)

        self.pieces = new_pieces

        actFs = self.move_pieces()
        if len(self.pieces) == 0:
            raise generic.ScriptError("Expected names and/or town_name references in the part.", self.pos)
        if len(self.pieces) > 255:
            raise generic.ScriptError("Too many values in a part, found %d, maximum is 255" % len(self.pieces), self.pos)

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
            return [] # Trivially correct.

        # There are too many pieces.
        prob_pieces = {}  # Dict of probability -> pieces
        non_removables = 0
        for piece in self.pieces:
            if piece.probability.value >= 1 + 0x7f // 2:
                non_removables = non_removables + 1
                continue # Moving such a piece is useless as at most one fits.

            pcs = prob_pieces.get(piece.probability.value)
            if pcs is None:
                pcs = []
                prob_pieces[piece.probability.value] = pcs
            pcs.append(piece)

        ordered_pieces = [(prob, pcs[:]) for prob, pcs in prob_pieces.iteritems()] # Ordered list of tuples (probability, pieces-with-that-value)
        ordered_pieces.sort()

        # Compute how many actionFs must be created (for movables only).
        nactf = 0
        count = len(self.pieces)
        while nactf < 255 - non_removables and count > 255 - non_removables - nactf:
            # Still too many, add another actionF
            nactf = nactf + 1
            sum_probs = 0

            # Put the biggest ones in, slowly going towards the smaller ones.
            i = len(ordered_pieces) - 1
            while i >= 0:
                while count > 255 - non_removables - nactf and len(ordered_pieces[i][1]) > 0 and ordered_pieces[i][0] <= 0x7f - sum_probs:
                    ordered_pieces[i][1].pop()
                    sum_probs += ordered_pieces[i][0]
                    count = count - 1

                i = i - 1

            if sum_probs == 0:
                return [] # Nothing was found, user should provide a better set

        subs = self.split_pieces(prob_pieces, nactf)
        if len(self.pieces) - sum(len(sub[1]) for sub in subs) > 255:
            # Perhaps nactf was too optimistic, let's try again.
            nactf = nactf + 1
            subs = self.split_pieces(prob_pieces, nactf)
            if len(self.pieces) - sum(len(sub[1]) for sub in subs) > 255:
                # Really not working, bail out.
                return []

        actFs = []
        for prob, sub in subs:
            actF_name = expression.Identifier("**townname #%d**" % townname_serial, None)
            townname_serial = townname_serial + 1
            parts = [TownNamesPart(sub, self.pos)]
            actF = actionF.ActionF(actF_name, None, None, parts, self.pos)
            actFs.append(actF)

            # Remove pieces of 'sub' from self.pieces
            counts = len(self.pieces), len(sub)
            sub_set = set(sub)
            self.pieces = [piece for piece in self.pieces if piece not in sub_set]
            assert len(self.pieces) == counts[0] - counts[1]

            self.pieces.append(TownNamesEntryDefinition(actF_name, expression.ConstantNumeric(prob), self.pos))

        # update self.parts
        return actFs

    def split_pieces(self, prob_pieces, n):
        """
        Split the pieces of L{prob_pieces} into L{n} new sub-actions.

        @param prob_pieces: Pieces available for splitting.
        @type  prob_pieces: C{dict} of C{int} to C{list} of (L{TownNamesEntryDefinition} or L{TownNamesEntryText})

        @param n: Number of sub-elements to check.
        @type  n: C{int}

        @return: Lists of tuples (total probability, pieces)
        @rtype:  C{list} of C{tuple} (C{int}, C{list} of (L{TownNamesEntryDefinition} or L{TownNamesEntryText}))
        """
        # Create heap of sub-actions.
        heap = []
        i = 0
        while i < n:
            heapq.heappush(heap, (0, []))
            i = i + 1

        ordered_pieces = [(prob, pcs[:]) for prob, pcs in prob_pieces.iteritems()] # Ordered list of tuples (probability, pieces-with-that-value)
        ordered_pieces.sort()
        ordered_pieces.reverse()
        for val, pcs in ordered_pieces:
            while len(pcs) > 0:
                sub = heapq.heappop(heap)
                if sub[0] + val > 0x7f:
                    heapq.heappush(heap, sub)
                    break

                sub[1].append(pcs.pop())
                sub = (sub[0] + val, sub[1])
                heapq.heappush(heap, sub)

        return heap



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

        self.startbit = startbit
        n = 1
        while total > (1 << n): n = n + 1
        self.num_bits = n
        return n

    def debug_print(self, indentation):
        total = sum(piece.probability.value for piece in self.pieces)
        print indentation*' ' + 'Town names part (total %d)' % total
        for piece in self.pieces:
            piece.debug_print(indentation + 2, total)

    def get_length(self):
        size = 3 # textcount, firstbit, bitcount bytes.
        size += sum(piece.get_length() for piece in self.pieces)
        return size

    def resolve_townname_id(self):
        '''
        Resolve the reference numbers to previous C{town_names} blocks.

        @return: Set of referenced C{town_names} block numbers.
        '''
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
            file.newline()


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
        self.number = None
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
