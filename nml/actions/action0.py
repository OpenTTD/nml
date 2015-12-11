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

from nml.actions.action0properties import BaseAction0Property, Action0Property, properties, two_byte_property
from nml import generic, expression, nmlop, grfstrings
from nml.actions import base_action, action4, action6, actionD, action7
from nml.ast import general

class BlockAllocation(object):
    """
    Administration of allocated blocks of a size, in a range of addresses.
    Blocks always start at address C{0}, but the first available freely usable
    address may be further.

    The allocation information is kept in L{allocated}. It has the following cases
    - An address does not exist in the dictionary.
      The address is free for use.
    - An address exists, with an integer number as size.
      At this address a block has been allocated with that size.
    - An address exists, with value C{None}.
      The address is part of an allocated block, but not the start.

    @ivar first: First freely usable address.
    @type first: C{int}

    @ivar last: Last freely usable address.
    @type last: C{int}

    @ivar name: Name for debug output.
    @type name: C{str}

    @ivar dynamic_allocation: True, if ids are allocated. False, if they refer to static entities.
    @type dynamic_allocation: C{bool}

    @ivar allocated: Mapping of allocated blocks.
    @type allocated: C{dict} of C{int} to allocation information.

    @ivar filled: Mapping of block size to smallest address that may contain free space.
                  Serves as a cache to speed up searches.
    @type filled: C{dict} of C{int}
    """
    def __init__(self, first, last, name, dynamic_allocation=True):
        self.first = first
        self.last = last
        self.name = name
        self.dynamic_allocation = dynamic_allocation
        self.allocated = {}
        self.filled = {}

    def get_num_allocated(self):
        """
        Return number of allocated ids.
        """
        if self.dynamic_allocation:
            return len(self.allocated)
        else:
            return 0

    def get_max_allocated(self):
        """
        Return maximum number of allocateable ids.
        """
        if self.dynamic_allocation:
            return self.last - self.first + 1
        else:
            return 0

    def in_range(self, addr, length):
        """
        Does a block starting at the provided address with the given length in
        the available address space?

        @param addr: First address of the block.
        @type  addr: C{int}

        @param length: Number of addresses in the block.
        @type  length: C{int}

        @return: Whether the block fits enitrely in the available address space.
        @rtype:  C{bool}
        """
        return addr >= 0 and addr + length - 1 <= self.last

    def get_size(self, addr):
        """
        Get the size of the block allocated at the given address.

        @param addr: Address being queried.
        @type  addr: C{int}

        @return: Size of the allocated block, if one was allocated here, else C{None}.
        @rtype:  C{int} or C{None}
        """
        return self.allocated.get(addr)

    def is_address_free(self, addr):
        """
        Is the space at the given address still available?
        ( cheaper variant of C{self.get_last_used(addr, 1) is None} )

        @param addr: Address being queried.
        @type  addr: C{int}

        @return: Whether the space at the provided address is available.
        @rtype:  C{bool}
        """
        return addr not in self.allocated

    def get_last_used(self, addr, length):
        """
        Check whether a block of addresses is used.

        @param addr: First address of the block.
        @type  addr: C{int}

        @param length: Number of addresses in the block.
        @type  length: C{int}

        @return: The last used address in the block, or C{None} if all addresses are free.
        @rtype:  C{int} or C{None}

        @precond: Addresses of the range should be within the available address space.
        """
        for idx in range(addr + length - 1, addr - 1, -1):
            if idx in self.allocated: return idx
        return None

    def mark_used(self, addr, length):
        """
        Mark an area as being allocated.

        @param addr: First address of the block.
        @type  addr: C{int}

        @param length: Number of addresses in the block.
        @type  length: C{int}

        @precond: Addresses of the block should be within the freely available address space.
        @precond: No address in the block may have been allocated.
        """
        self.allocated[addr] = length
        for idx in range(addr + 1, addr + length):
            self.allocated[idx] = None

    def find_unused(self, length):
        """
        Find an area of unused space.

        @param length: Number of addresses to find.
        @type  length: C{int}

        @return: Address in the freely available address space for the new block,
                 or C{None} if no space is available.
        @rtype:  C{int} or C{None}
        """
        idx = self.filled.get(length)
        if idx is None:
            # Never searched before with this block size.
            # Start at the biggest offset previously discovered with a smaller block size.
            smaller_filleds = [min_f for sz, min_f in self.filled.items() if sz < length]
            idx = self.first if len(smaller_filleds) == 0 else max(smaller_filleds)

        last_idx = self.last - length + 1
        while idx < last_idx:
            last_used = self.get_last_used(idx, length)
            if last_used is None:
                self.filled[length] = idx + length
                return idx

            idx = last_used + 1

        return None

# Available IDs for each feature.
# Maximum allowed id (houses and indtiles in principle allow up to 511, but action3 does not accept extended bytes).
used_ids = [
    BlockAllocation(116, 0xFFFF, "Train"),
    BlockAllocation( 88, 0xFFFF, "Road Vehicle"),
    BlockAllocation( 11, 0xFFFF, "Ship"),
    BlockAllocation( 41, 0xFFFF, "Aircraft"),
    BlockAllocation(  0,    255, "Station"),
    BlockAllocation(  0,      8, "Canal", False),
    BlockAllocation(  0,     15, "Bridge", False),
    BlockAllocation(  0,    255, "House"),
    BlockAllocation(  0,     -1, "Global", False),
    BlockAllocation(  0,    255, "Industry Tile"),
    BlockAllocation(  0,    127, "Industry"),
    BlockAllocation(  0,     31, "Cargo"),
    BlockAllocation(  0,     -1, "Sound"),
    BlockAllocation(  0,    127, "Airport"),
    BlockAllocation(  0,     -1, "Signal", False),
    BlockAllocation(  0,    255, "Object"),
    BlockAllocation(  0,     15, "Railtype"),
    BlockAllocation(  0,    255, "Airport Tile"),
]

def print_stats():
    """
    Print statistics about used ids.
    """
    for feature in used_ids:
        used = feature.get_num_allocated()
        if used > 0 and feature.dynamic_allocation:
            generic.print_info("{} items: {}/{}".format(feature.name, used, feature.get_max_allocated()))

def mark_id_used(feature, id, num_ids):
    """
    Mark a range of ids as used.

    @param feature: Feature of the ids.
    @type  feature: C{int}

    @param id: First id to be marked.
    @type  id: C{int}

    @param num_ids: Number of ids to mark as used, starting with \a id.
    @type  num_ids: C{int}
    """
    used_ids[feature].mark_used(id, num_ids)


def check_id_range(feature, id, num_ids, pos):
    """
    Check that the id is valid, and is either free or points to an already allocated block.

    @param feature: Feature of the ids.
    @type  feature: C{int}

    @param id: Base id number.
    @type  id: C{int}

    @param num_ids: Number of ids to test, starting with \a id.
    @type  num_ids: C{int}

    @param pos: Source position of the check, for reporting errors.
    @type  pos: L{Position}

    @return: Whether the block was allocated already.
    @rtype:  C{bool}
    """
    blk_alloc = used_ids[feature]

    # Check that IDs are valid and in range.
    if not blk_alloc.in_range(id, num_ids):
        msg = "Item ID must be in range 0..{:d}, encountered {:d}..{:d}."
        msg = msg.format(blk_alloc.last, id, id + num_ids - 1)
        raise generic.ScriptError(msg, pos)

    # ID already defined, but with the same size: OK
    if blk_alloc.get_size(id) == num_ids: return True

    # All IDs free: no problem.
    if blk_alloc.get_last_used(id, num_ids) is None: return False

    # No space at the indicated position, report an error.

    if blk_alloc.get_size(id) is not None:
        # ID already defined with a different size: error.
        raise generic.ScriptError("Item with ID {:d} has already been defined, but with a different size.".format(id), pos)

    if blk_alloc.is_address_free(id):
        # First item id free -> any of the additional tile ids must be blocked.
        msg = "This multi-tile house requires that item IDs {:d}..{:d} are free, but they are not."
        msg = msg.format(id, id + num_ids - 1)
        raise generic.ScriptError(msg, pos)

    # ID already defined as part of a multi-tile house.
    raise generic.ScriptError("Item ID {:d} has already used as part of a multi-tile house.".format(id), pos)

def get_free_id(feature, num_ids, pos):
    """
    Find an id to allocate a range of \a num_ids ids in a feature.

    @param feature: Feature of the ids.
    @type  feature: C{int}

    @param num_ids: Number of ids to allocate.
    @type  num_ids: C{int}

    @param pos: Position information.
    @type  pos: L{Position}
    """
    blk_alloc = used_ids[feature]

    addr = blk_alloc.find_unused(num_ids)
    if addr is None:
        msg = "Unable to allocate ID for item, no more free IDs available (maximum is {:d})"
        msg = msg.format(blk_alloc.last)
        raise generic.ScriptError(msg, pos)

    blk_alloc.mark_used(addr, num_ids)
    return addr

# Number of tiles for various house sizes
house_sizes = {
    0 : 1, # 1x1
    2 : 2, # 2x1
    3 : 2, # 1x2
    4 : 4, # 2x2
}

def adjust_value(value, org_value, unit, ottd_convert_func):
    """
    Make sure that the property value written to the NewGRF will match exactly
    the value as quoted

    @param value: The value to check, converted to base units
    @type value: L{Expression}

    @param org_value: The original value as written in the input file
    @type org_value: L{Expression}

    @param unit: The unit of the org_value
    @type unit: L{Unit} or C{None}

    @return: The adjusted value
    @rtype: L{Expression}
    """
    while ottd_convert_func(value, unit) > org_value.value:
        value = expression.ConstantNumeric(int(value.value - 1), value.pos)
    lower_value = value
    while ottd_convert_func(value, unit) < org_value.value:
        value = expression.ConstantNumeric(int(value.value + 1), value.pos)
    higher_value = value

    if abs(ottd_convert_func(lower_value, unit) - org_value.value) < abs(ottd_convert_func(higher_value, unit) - org_value.value):
        return lower_value
    return higher_value

class Action0(base_action.BaseAction):
    """
    Representation of NFO action 0. Action 0 is used to set properties on all
    kinds of objects. It can set any number of properties on a list of
    consecutive IDs. Each property is defined by a unique (per feature) integer.

    @ivar feature: Feature number to set properties for.
    @type feature: C{int}

    @ivar id: First ID to set properties for
    @type id: C{int}

    @ivar prop_list: List of all properties that are to be set.
    @type prop_list: C{list} of L{BaseAction0Property}

    @ivar num_ids: Number of IDs to set properties for.
    @type num_ids: C{int} or C{None}
    """
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.prop_list = []
        self.num_ids = None

    def prepare_output(self, sprite_num):
        if self.num_ids is None: self.num_ids = 1

    def write(self, file):
        size = 7
        for prop in self.prop_list:
            assert isinstance(prop, BaseAction0Property), type(prop)
            if isinstance(prop, Action0Property):
                assert len(prop.values) == self.num_ids
            size += prop.get_size()
        file.start_sprite(size)
        file.print_bytex(0)
        file.print_bytex(self.feature)
        file.print_byte(len(self.prop_list))
        file.print_bytex(self.num_ids)
        file.print_bytex(0xFF)
        file.print_wordx(self.id)
        file.newline()
        for prop in self.prop_list:
            prop.write(file)
        file.end_sprite()


def create_action0(feature, id, act6, action_list):
    """
    Create an action0 with variable id

    @param feature: Feature of the action0
    @type feature: C{int}

    @param id: ID of the corresponding item
    @type id: L{Expression}

    @param act6: Action6 to add any modifications to
    @type act6: L{Action6}

    @param action_list: Action list to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @return: A tuple of (resulting action0, offset to use for action6)
    @rtype: C{tuple} of (L{Action0}, C{int})
    """
    id, offset = actionD.write_action_value(id, action_list, act6, 5, 2)

    action0 = Action0(feature, id.value)
    return (action0, offset)

def get_property_info_list(feature, name):
    """
    Find information on a single property, based on feature and name/number

    @param feature: Feature of the associated item
    @type feature: C{int}

    @param name: Name (or number) of the property
    @type name: L{Identifier} or L{ConstantNumeric}

    @return: A list of dictionaries with property information
    @rtype: C{list} of C{dict}
    """
    global properties

    #Validate feature
    assert feature in range (0, len(properties)) #guaranteed by item
    if properties[feature] is None:
        raise generic.ScriptError("Setting properties for feature '{}' is not possible, no properties are defined.".format(general.feature_name(feature)), name.pos)

    if isinstance(name, expression.Identifier):
        if not name.value in properties[feature]: raise generic.ScriptError("Unknown property name: " + name.value, name.pos)
        prop_info_list = properties[feature][name.value]
        if not isinstance(prop_info_list, list): prop_info_list = [prop_info_list]
    elif isinstance(name, expression.ConstantNumeric):
        for p in properties[feature]:
            prop_info_list = properties[feature][p]
            if not isinstance(prop_info_list, list): prop_info_list = [prop_info_list]
            # Only non-compound properties may be set by number
            if len(prop_info_list) == 1 and 'num' in prop_info_list[0] and prop_info_list[0]['num'] == name.value:
                break
        else:
            raise generic.ScriptError("Unknown property number: " + str(name), name.pos)
    else: assert False

    for prop_info in prop_info_list:
        if 'warning' in prop_info:
            generic.print_warning(prop_info['warning'], name.pos)
    return prop_info_list

def parse_property_value(prop_info, value, unit = None, size_bit = None):
    """
    Parse a single property value / unit
    To determine the value that is to be used in nfo

    @param prop_info: A dictionary with property information
    @type prop_info: C{dict}

    @param value: Value of the property
    @type value: L{Expression}

    @param unit: Unit of the property value (e.g. km/h)
    @type unit: L{Unit} or C{None}

    @param size_bit: Bit that indicates the size of a multitile house
                     Set iff the item is a house
    @type size_bit: C{int} or C{None}

    @return: List of values to actually use (in nfo) for the property
    @rtype: L{Expression}
    """
    # Change value to use, except when the 'nfo' unit is used
    if unit is None or unit.type != 'nfo':
        # Save the original value to test conversion against it
        org_value = value

        # Multiply by property-specific conversion factor
        mul, div = 1, 1
        if 'unit_conversion' in prop_info:
            mul = prop_info['unit_conversion']
            if isinstance(mul, tuple):
                mul, div = mul

        # Divide by conversion factor specified by unit
        if unit is not None:
            if not 'unit_type' in prop_info or unit.type != prop_info['unit_type']:
                raise generic.ScriptError("Invalid unit for property", value.pos)
            unit_mul, unit_div = unit.convert, 1
            if isinstance(unit_mul, tuple):
                unit_mul, unit_div = unit_mul
            mul *= unit_div
            div *= unit_mul

        # Factor out common factors
        gcd = generic.greatest_common_divisor(mul, div)
        mul //= gcd
        div //= gcd

        if isinstance(value, (expression.ConstantNumeric, expression.ConstantFloat)):
            # Even if mul == div == 1, we have to round floats and adjust value
            value = expression.ConstantNumeric(int(float(value.value) * mul / div + 0.5), value.pos)
            if unit is not None and 'adjust_value' in prop_info:
                value = adjust_value(value, org_value, unit, prop_info['adjust_value'])
        elif mul != div:
            # Compute (value * mul + div/2) / div
            value = expression.BinOp(nmlop.MUL, value, expression.ConstantNumeric(mul, value.pos), value.pos)
            value = expression.BinOp(nmlop.ADD, value, expression.ConstantNumeric(int(div / 2), value.pos), value.pos)
            value = expression.BinOp(nmlop.DIV, value, expression.ConstantNumeric(div, value.pos), value.pos)

    elif isinstance(value, expression.ConstantFloat):
        # Round floats to ints
        value = expression.ConstantNumeric(int(value.value + 0.5), value.pos)

    # Apply value_function if it exists
    if 'value_function' in prop_info:
        value = prop_info['value_function'](value)

    # Make multitile houses work
    if size_bit is not None:
        num_ids = house_sizes[size_bit]
        assert 'multitile_function' in prop_info
        ret = prop_info['multitile_function'](value, num_ids, size_bit)
        assert len(ret) == num_ids
        return ret
    else:
        return [value]

def parse_property(prop_info, value_list, feature, id):
    """
    Parse a single property

    @param prop_info: A dictionary with property information
    @type prop_info: C{dict}

    @param value_list: List of values for the property, with unit conversion applied
    @type value_list: C{list} of L{Expression}

    @param feature: Feature of the associated item
    @type feature: C{int}

    @param id: ID of the associated item
    @type id: L{Expression}

    @return: A tuple containing the following:
                - List of properties to add to the action 0
                - List of actions to prepend
                - List of modifications to apply via action 6
                - List of actions to append
    @rtype: C{tuple} of (C{list} of L{Action0Property}, C{list} of L{BaseAction}, C{list} of 3-C{tuple}, C{list} of L{BaseAction})
    """
    action_list = []
    action_list_append = []
    mods = []

    if 'custom_function' in prop_info:
        props = prop_info['custom_function'](*value_list)
    else:
        # First process each element in the value_list
        final_values = []
        for i, value in enumerate(value_list):
            if 'string_literal' in prop_info and (isinstance(value, expression.StringLiteral) or prop_info['string_literal'] != 4):
                # Parse non-string exprssions just like integers. User will have to take care of proper value.
                # This can be used to set a label (=string of length 4) to the value of a parameter.
                if not isinstance(value, expression.StringLiteral): raise generic.ScriptError("Value for property {:d} must be a string literal".format(prop_info['num']), value.pos)
                if len(value.value) != prop_info['string_literal']:
                    raise generic.ScriptError("Value for property {:d} must be of length {:d}".format(prop_info['num'], prop_info['string_literal']), value.pos)

            elif isinstance(value, expression.ConstantNumeric):
                pass

            elif isinstance(value, expression.Parameter) and isinstance(value.num, expression.ConstantNumeric):
                mods.append( (value.num.value, prop_info['size'], i * prop_info['size'] + 1) )
                value = expression.ConstantNumeric(0)

            elif isinstance(value, expression.String):
                if not 'string' in prop_info: raise generic.ScriptError("String used as value for non-string property: " + str(prop_info['num']), value.pos)
                string_range = prop_info['string']
                stringid, string_actions = action4.get_string_action4s(feature, string_range, value, id)
                value = expression.ConstantNumeric(stringid)
                action_list_append.extend(string_actions)

            else:
                tmp_param, tmp_param_actions = actionD.get_tmp_parameter(value)
                mods.append((tmp_param, prop_info['size'], i * prop_info['size'] + 1))
                action_list.extend(tmp_param_actions)
                value = expression.ConstantNumeric(0)

            final_values.append(value)

        # Now, write a single Action0 Property with all of these values
        if prop_info['num'] != -1:
            props = [Action0Property(prop_info['num'], final_values, prop_info['size'])]
        else:
            props = []

    return (props, action_list, mods, action_list_append)

def validate_prop_info_list(prop_info_list, pos_list, feature):
    """
    Perform various checks on a list of properties in a property-block
        - make sure that properties that should appear first (substitute type) appear first

    @param prop_info_list: List of dictionaries with property information
    @type prop_info_list: C{list} of C{dict}

    @param pos_list: List containing position information (order matches prop_info_list)
    @type pos_list: C{list} of L{Position}

    @param feature: Feature of the associated item
    @type feature: C{int}
    """
    global properties
    first_warnings = [(info, pos_list[i]) for i, info in enumerate(prop_info_list) if 'first' in info and i != 0]
    for info, pos in first_warnings:
        for prop_name, prop_info in list(properties[feature].items()):
            if info == prop_info or (isinstance(prop_info, list) and info in prop_info):
                generic.print_warning("Property '{}' should be set before all other properties and graphics.".format(prop_name), pos)
                break


def parse_property_block(prop_list, feature, id, size):
    """
    Parse a property block to an action0 (with possibly various other actions)

    @param prop_list: List of properties to parse
    @type prop_list: C{list} of L{Property}

    @param feature: Feature of the associated item
    @type feature: C{int}

    @param id: ID of the associated item
    @type id: L{Expression}

    @param size: Size (for houses only)
    @type size: L{ConstantNumeric} or C{None}

    @return: List of resulting actions
    @rtype: C{list} of L{BaseAction}
    """
    action6.free_parameters.save()
    action_list = []
    action_list_append = []
    act6 = action6.Action6()

    action0, offset = create_action0(feature, id, act6, action_list)
    if feature == 0x07:
        size_bit = size.value if size is not None else 0
        action0.num_ids = house_sizes[size_bit]
    else:
        size_bit = None
        action0.num_ids = 1

    prop_info_list = []
    value_list_list = []
    pos_list = []
    for prop in prop_list:
        new_prop_info_list = get_property_info_list(feature, prop.name)
        prop_info_list.extend(new_prop_info_list)
        value_list_list.extend(parse_property_value(prop_info, prop.value, prop.unit, size_bit) for prop_info in new_prop_info_list)
        pos_list.extend(prop.name.pos for i in prop_info_list)

    validate_prop_info_list(prop_info_list, pos_list, feature)

    for prop_info, value_list in zip(prop_info_list, value_list_list):
        if 'test_function' in prop_info and not prop_info['test_function'](*value_list): continue
        properties, extra_actions, mods, extra_append_actions = parse_property(prop_info, value_list, feature, id)
        action_list.extend(extra_actions)
        action_list_append.extend(extra_append_actions)
        for mod in mods:
            act6.modify_bytes(mod[0], mod[1], mod[2] + offset)
        for p in properties:
            offset += p.get_size()
        action0.prop_list.extend(properties)

    if len(act6.modifications) > 0: action_list.append(act6)
    if len(action0.prop_list) != 0:
        action_list.append(action0)

    action_list.extend(action_list_append)

    action6.free_parameters.restore()
    return action_list

class IDListProp(BaseAction0Property):
    def __init__(self, prop_num, id_list):
        self.prop_num = prop_num
        self.id_list = id_list

    def write(self, file):
        file.print_bytex(self.prop_num)
        for i, id_val in enumerate(self.id_list):
            if i > 0 and i % 5 == 0: file.newline()
            file.print_string(id_val.value, False, True)
        file.newline()

    def get_size(self):
        return len(self.id_list) * 4 + 1

def get_cargolist_action(cargo_list):
    action0 = Action0(0x08, 0)
    action0.prop_list.append(IDListProp(0x09, cargo_list))
    action0.num_ids = len(cargo_list)
    return [action0]

def get_railtypelist_action(railtype_list):
    action6.free_parameters.save()
    act6 = action6.Action6()

    action_list = []
    action0, offset = create_action0(0x08, expression.ConstantNumeric(0), act6, action_list)
    id_table = []
    offset += 1 # Skip property number
    for railtype in railtype_list:
        if isinstance(railtype, expression.StringLiteral):
            id_table.append(railtype)
            offset+=4
            continue
        param, extra_actions = actionD.get_tmp_parameter(expression.ConstantNumeric(expression.parse_string_to_dword(railtype[-1])))
        action_list.extend(extra_actions)
        for idx in range(len(railtype)-2, -1, -1):
            val = expression.ConstantNumeric(expression.parse_string_to_dword(railtype[idx]))
            action_list.append(action7.SkipAction(0x09, 0x00, 4, (0x0D, None), val.value, 1))
            action_list.append(actionD.ActionD(expression.ConstantNumeric(param), expression.ConstantNumeric(0xFF), nmlop.ASSIGN, expression.ConstantNumeric(0xFF), val))
        act6.modify_bytes(param, 4, offset)
        id_table.append(expression.StringLiteral(r"\00\00\00\00", None))
        offset += 4
    action0.prop_list.append(IDListProp(0x12, id_table))
    action0.num_ids = len(railtype_list)

    if len(act6.modifications) > 0: action_list.append(act6)

    action_list.append(action0)
    action6.free_parameters.restore()
    return action_list

class ByteListProp(BaseAction0Property):
    def __init__(self, prop_num, data):
        self.prop_num = prop_num
        self.data = data

    def write(self, file):
        file.print_bytex(self.prop_num)
        file.newline()
        for i, data_val in enumerate(self.data):
            if i > 0 and i % 8 == 0: file.newline()
            file.print_bytex(ord(data_val))
        file.newline()

    def get_size(self):
        return len(self.data) + 1

def get_snowlinetable_action(snowline_table):
    assert len(snowline_table) == 12*32

    action6.free_parameters.save()
    action_list = []
    tmp_param_map = {} #Cache for tmp parameters
    act6 = action6.Action6()

    act0, offset = create_action0(0x08, expression.ConstantNumeric(0), act6, action_list)
    act0.num_ids = 1
    offset += 1 # Skip property number

    data_table = []
    idx = 0
    while idx < len(snowline_table):
        val = snowline_table[idx]
        if isinstance(val, expression.ConstantNumeric):
            data_table.append(val.value)
            idx += 1
            continue

        if idx + 3 >= len(snowline_table):
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(val)
            tmp_param_map[val] = tmp_param
            act6.modify_bytes(tmp_param, 1, offset + idx)
            action_list.extend(tmp_param_actions)
            data_table.append(0)
            idx += 1
            continue

        # Merge the next 4 values together in a single parameter.
        val2 = expression.BinOp(nmlop.SHIFT_LEFT, snowline_table[idx + 1], expression.ConstantNumeric(8))
        val3 = expression.BinOp(nmlop.SHIFT_LEFT, snowline_table[idx + 2], expression.ConstantNumeric(16))
        val4 = expression.BinOp(nmlop.SHIFT_LEFT, snowline_table[idx + 3], expression.ConstantNumeric(24))
        expr = expression.BinOp(nmlop.OR, val, val2)
        expr = expression.BinOp(nmlop.OR, expr, val3)
        expr = expression.BinOp(nmlop.OR, expr, val4)
        expr = expr.reduce()

        #Cache lookup, saves some ActionDs
        if expr in tmp_param_map:
            tmp_param, tmp_param_actions = tmp_param_map[expr], []
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
            tmp_param_map[expr] = tmp_param

        act6.modify_bytes(tmp_param, 4, offset + idx)
        action_list.extend(tmp_param_actions)
        data_table.extend([0, 0, 0, 0])
        idx += 4


    act0.prop_list.append(ByteListProp(0x10, ''.join([chr(x) for x in data_table])))
    if len(act6.modifications) > 0: action_list.append(act6)
    action_list.append(act0)
    action6.free_parameters.restore()
    return action_list

def get_basecost_action(basecost):
    action6.free_parameters.save()
    action_list = []
    tmp_param_map = {} #Cache for tmp parameters

    #We want to avoid writing lots of action0s if possible
    i = 0
    while i < len(basecost.costs):
        cost = basecost.costs[i]
        act6 = action6.Action6()

        act0, offset = create_action0(0x08, cost.name, act6, action_list)
        first_id = cost.name.value if isinstance(cost.name, expression.ConstantNumeric) else None

        num_ids = 1 #Number of values that will be written in one go
        values = []
        #try to capture as much values as possible
        while True:
            cost = basecost.costs[i]
            if isinstance(cost.value, expression.ConstantNumeric):
                values.append(cost.value)
            else:
                #Cache lookup, saves some ActionDs
                if cost.value in tmp_param_map:
                    tmp_param, tmp_param_actions = tmp_param_map[cost.value], []
                else:
                    tmp_param, tmp_param_actions = actionD.get_tmp_parameter(cost.value)
                    tmp_param_map[cost.value] = tmp_param
                act6.modify_bytes(tmp_param, 1, offset + num_ids)
                action_list.extend(tmp_param_actions)
                values.append(expression.ConstantNumeric(0))

            #check if we can append the next to this one (it has to be consecutively numbered)
            if first_id is not None and (i + 1) < len(basecost.costs):
                nextcost = basecost.costs[i+1]
                if isinstance(nextcost.name, expression.ConstantNumeric) and nextcost.name.value == first_id + num_ids:
                    num_ids += 1
                    i += 1
                    #Yes We Can, continue the loop to append this value to the list and try further
                    continue
            # No match, so stop it and write an action0
            break

        act0.prop_list.append(Action0Property(0x08, values, 1))
        act0.num_ids = num_ids
        if len(act6.modifications) > 0: action_list.append(act6)
        action_list.append(act0)
        i += 1
    action6.free_parameters.restore()
    return action_list

class LanguageTranslationTable(BaseAction0Property):
    def __init__(self, num, name_list, extra_names):
        self.num = num
        self.mappings = []
        for name, idx in list(name_list.items()):
            self.mappings.append( (idx, name) )
            if name in extra_names:
                for extra_name in extra_names[name]:
                    self.mappings.append( (idx, extra_name) )
        # Sort to keep the output deterministic
        self.mappings.sort()

    def write(self, file):
        file.print_bytex(self.num)
        for mapping in self.mappings:
            file.print_bytex(mapping[0])
            file.print_string(mapping[1])
        file.print_bytex(0)
        file.newline()

    def get_size(self):
        size = 2
        for mapping in self.mappings:
            size += 1 + grfstrings.get_string_size(mapping[1])
        return size

def get_language_translation_tables(lang):
    action0 = Action0(0x08, lang.langid)
    if lang.genders is not None:
        action0.prop_list.append(LanguageTranslationTable(0x13, lang.genders, lang.gender_map))
    if lang.cases is not None:
        action0.prop_list.append(LanguageTranslationTable(0x14, lang.cases, lang.case_map))
    if lang.plural is not None:
        action0.prop_list.append(Action0Property(0x15, expression.ConstantNumeric(lang.plural), 1))
    if len(action0.prop_list) > 0:
        return [action0]
    return []

disable_info = {
    # Vehicles: set climates_available to 0
    0x00 : {'num': 116, 'props': [{'num': 0x06, 'size': 1, 'value': 0}]},
    0x01 : {'num':  88, 'props': [{'num': 0x06, 'size': 1, 'value': 0}]},
    0x02 : {'num':  11, 'props': [{'num': 0x06, 'size': 1, 'value': 0}]},
    0x03 : {'num':  41, 'props': [{'num': 0x06, 'size': 1, 'value': 0}]},

    # Houses / industries / airports: Set substitute_type to FF
    0x07 : {'num': 110, 'props': [{'num': 0x08, 'size': 1, 'value': 0xFF}]},
    0x0A : {'num':  37, 'props': [{'num': 0x08, 'size': 1, 'value': 0xFF}]},
    0x0D : {'num':  10, 'props': [{'num': 0x08, 'size': 1, 'value': 0xFF}]},

    # Cargos: Set bitnum to FF and label to 0
    0x0B : {'num':  27, 'props': [{'num': 0x08, 'size': 1, 'value': 0xFF}, {'num': 0x17, 'size': 4, 'value': 0}]},
}

def get_disable_actions(disable):
    """
    Get the action list for a disable_item block

    @param disable: Disable block
    @type disable: L{DisableItem}

    @return: A list of resulting actions
    @rtype: C{list} of L{BaseAction}
    """
    feature = disable.feature.value
    if feature not in disable_info:
        raise generic.ScriptError("disable_item() is not available for feature {:d}.".format(feature), disable.pos)
    if disable.first_id is None:
        # No ids set -> disable all
        assert disable.last_id is None
        first = 0
        num = disable_info[feature]['num']
    else:
        first = disable.first_id.value
        if disable.last_id is None:
            num = 1
        else:
            num = disable.last_id.value - first + 1

    act0 = Action0(feature, first)
    act0.num_ids = num
    for prop in disable_info[feature]['props']:
        act0.prop_list.append(Action0Property(prop['num'], num * [expression.ConstantNumeric(prop['value'])], prop['size']))

    return [act0]

class EngineOverrideProp(BaseAction0Property):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def write(self, file):
        file.print_bytex(0x11)
        file.print_dwordx(self.source)
        file.print_dwordx(self.target)
        file.newline()

    def get_size(self):
        return 9

def get_engine_override_action(override):
    act0 = Action0(0x08, 0)
    act0.num_ids = 1
    act0.prop_list.append(EngineOverrideProp(override.source_grfid, override.grfid))
    return [act0]

def parse_sort_block(feature, vehid_list):
    prop_num = [0x1A, 0x20, 0x1B, 0x1B]
    action_list = []
    if len(vehid_list) >= 2:
        last = vehid_list[0]
        idx = len(vehid_list) - 1
        while idx >= 0:
            cur = vehid_list[idx]
            prop = Action0Property(prop_num[feature], [last], 3)
            action_list.append(Action0(feature, cur.value))
            action_list[-1].prop_list.append(prop)
            last = cur
            idx -= 1
    return action_list

callback_flag_properties = {
    0x00: {'size': 1, 'num': 0x1E},
    0x01: {'size': 1, 'num': 0x17},
    0x02: {'size': 1, 'num': 0x12},
    0x03: {'size': 1, 'num': 0x14},
    0x05: {'size': 1, 'num': 0x08},
    0x07: two_byte_property(0x14, 0x1D),
    0x09: {'size': 1, 'num': 0x0E},
    0x0A: two_byte_property(0x21, 0x22),
    0x0B: {'size': 1, 'num': 0x1A},
    0x0F: {'size': 2, 'num': 0x15},
    0x11: {'size': 1, 'num': 0x0E},
}

def get_callback_flags_actions(feature, id, flags):
    """
    Get a list of actions to set the callback flags of a certain item

    @param feature: Feature of the item
    @type feature: C{int}

    @param id: ID of the item
    @type id: L{Expression}

    @param flags: Value of the 'callback_flags' property
    @type flags: C{int}

    @return: A list of actions
    @rtype: C{list} of L{BaseAction}
    """
    assert isinstance(id, expression.ConstantNumeric)
    act0, offset = create_action0(feature, id, None, None)
    act0.num_ids = 1
    assert feature in callback_flag_properties

    prop_info_list = callback_flag_properties[feature]
    if not isinstance(prop_info_list, list): prop_info_list = [prop_info_list]
    for prop_info in prop_info_list:
        act0.prop_list.append(Action0Property(prop_info['num'], parse_property_value(prop_info, expression.ConstantNumeric(flags)), prop_info['size']))

    return [act0]

def get_volume_actions(volume_list):
    """
    Get a list of actions to set sound volumes

    @param volume_list: List of (sound id, volume) tuples, sorted in ascending order
    @type volume_list: C{list} of (C{int}, C{int})-tuples

    @return: A list of actions
    @rtype: C{list} of L{BaseAction}
    """
    action_list = []
    first_id = None # First ID in a series of consecutive IDs
    value_series = [] # Series of values to write in a single action

    for id, volume in volume_list:
        if first_id is None:
            first_id = id
        continue_series = first_id + len(value_series) == id
        if continue_series:
            value_series.append(volume)

        if not continue_series or id == volume_list[-1][0]:
            # Write action for this series
            act0, offset = create_action0(0x0C, expression.ConstantNumeric(first_id), None, None)
            act0.num_ids = len(value_series)
            act0.prop_list.append(Action0Property(0x08, [expression.ConstantNumeric(v) for v in value_series], 1))
            action_list.append(act0)

            # start new series, if needed
            if not continue_series:
                first_id = id
                value_series = [volume]

    return action_list


