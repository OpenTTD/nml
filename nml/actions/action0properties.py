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

import itertools
from nml import generic, nmlop
from nml.expression import BinOp, ConstantNumeric, ConstantFloat, Array, StringLiteral, Identifier

tilelayout_names = {}

class BaseAction0Property(object):
    """
    Base class for Action0 properties.
    """

    def write(self, file):
        """
        Write this property to the output given by file.

        @param file: The outputfile we have to write to.
        @type  file: L{BinaryOutputBase}
        """
        raise NotImplementedError('write is not implemented in %r' % type(self))

    def get_size(self):
        """
        Get the number of bytes that this property will write to
        the output.

        @return: The size of this property in bytes.
        @rtype:  C{int}
        """
        raise NotImplementedError('get_size is not implemented in %r' % type(self))

class Action0Property(BaseAction0Property):
    """
    Simple Action 0 property with a fixed size.

    @ivar num: Number of the property.
    @type num: C{int}

    @ivar values: Value of the property for each id.
    @type values: C{list} of L{ConstantNumeric}

    @ivar size: Size of the storage, in bytes.
    @type size: C{int}
    """
    def __init__(self, num, value, size):
        self.num = num
        self.values = value if isinstance(value, list) else [value]
        self.size = size

        # Make sure the value fits in the size.
        # Strings have their own check in parse_property
        for val in self.values:
            if not isinstance(val, StringLiteral):
                biggest = 1 << (8 * size)
                if val.value >= biggest:
                    raise generic.ScriptError("Action 0 property too large", val.pos)
                elif val.value < 0 and val.value + (biggest / 2) < 0:
                    raise generic.ScriptError("Action 0 property too small", val.pos)

    def write(self, file):
        file.print_bytex(self.num)
        for val in self.values:
            val.write(file, self.size)
        file.newline()

    def get_size(self):
        return self.size * len(self.values) + 1

# @var properties: A mapping of features to properties. This is a list
# with one item per feature. Entries should be a dictionary of properties,
# or C{None} if no properties are defined for that feature.
#
# Each property is a mapping of property name to its characteristics.
# These characteristics are either a dictionary or a list of
# dictionaries, the latter can be used to set multiple properties.
# First a short summary is given, then the recognized characteristics
# are outlined below in more detail.
#
# Summary: If 'string' or 'string_literal' is set, the value should be a
# string or literal string, else the value is a number. 'unit_type' and
# 'unit_conversion' are used to convert user-entered values to nfo values.
# If some more arithmetic is needed to convert the entered value into an nfo
# value, 'value_function' can be used. For even more complicated things,
# 'custom_function' can be used to create a special mapping of the value to nfo
# properties, else 'num' and 'size' are used to provide a 'normal' action0.
#
# 'string', if set, means that the value of the property should be a string.
# The value of characteristic indicates the string range to use (usually 0xD0 or 0xDC)
# If set to None, the string will use the ID of the item (used for vehicle names)
#
# 'string_literal', if set, indicates that the value of the property should
# be a literal (quoted) string. The value of the characteristic is equal to
# the required length (usually 4) of said literal string.
#
# 'unit_type' means that units of the given type (power, speed) can be applied
# to this property. A list of units can be found in ../unit.py. The value is then
# converted to a certain reference unit (for example m/s for speed)
# Leaving this unset means that no units (except 'nfo' which is an identity mapping)
# can be applied to this property.
#
# 'unit_conversion' defines a conversion factor between the value entered by
# the user and the resulting value in nfo. This is either an integer or a
# rational number entered as a 2-tuple (numerator, denominator).
# The entered value (possibly converted # to the appropriate reference unit,
# see 'unit_type' above) is multiplied by this factor and then rounded to an
# integer to provide the final value.
# This parameter is not required and defaults to 1.
#
# 'value_function' can be used to alter the mapping of nml values to nfo values
# it takes one argument (the value) and returns the new value to use
# Both the parameter and the return value are expressions that do not have to be
# constants
#
# 'custom_function' can be used to bypass the normal way of converting the
# name / value to an Action0Property. This function is normally called with one
# argument, which is the value of the property. For houses, there may be multiple
# values, passed as a vararg-list. It should return a list of Action0Property.
# To pass extra parameters to the function, a dose of lambda calculus can be used.
# Consult the code for examples.
#
# 'test_function' can be used to determine if the property should be set in the
# first place. It normally takes one argument (the value) and should return True
# if the property is to be set, False if it is to be ignored. Default is True
# For houses, there may be multiple values, passed as a vararg-list.
#
# 'num' is the Action0 property number of the action 0 property, as given by the
# nfo specs. If set to -1, no action0 property will be generated. If
# 'custom_function' is set, this value is not needed and can be left out.
#
# 'size' is the size (in bytes) of the resulting action 0 property. Valid
# values are 1 (byte), 2 (word) or 4 (dword). For other (or variable) sizes,
# 'custom_function' is needed. If 'custom_function' is set or 'num' is equal
# to -1, this parameter is not needed and can be left out.
#
# 'warning' is a string (optional) containing a warning message that will be
# shown if a property is used. Use for deprecating properties.
#
# 'first' (value doesn't matter) if the property should be set first (generally a substitute type)

properties = 0x12 * [None]

#
# Some helper functions that are used for multiple features
#

def two_byte_property(low_prop, high_prop, low_prop_info = {}, high_prop_info = {}):
    """
    Decode a two byte value into two action 0 properties.

    @param low_prop: Property number for the low 8 bits of the value.
    @type  low_prop: C{int}

    @param high_prop: Property number for the high 8 bits of the value.
    @type  high_prop: C{int}

    @param low_prop_info: Dictionary with additional property information for the low byte.
    @type low_prop_info: C{dict}

    @param high_prop_info: Dictionary with additional property information for the low byte.
    @type high_prop_info: C{dict}

    @return: Sequence of two dictionaries with property information (low part, high part).
    @rtype:  C{list} of C{dict}
    """
    low_byte_info = {'num': low_prop, 'size': 1, 'value_function': lambda value: BinOp(nmlop.AND, value, ConstantNumeric(0xFF, value.pos), value.pos).reduce()}
    high_byte_info = {'num': high_prop, 'size': 1, 'value_function': lambda value: BinOp(nmlop.SHIFT_RIGHT, value, ConstantNumeric(8, value.pos), value.pos).reduce()}
    low_byte_info.update(low_prop_info)
    high_byte_info.update(high_prop_info)
    return [low_byte_info, high_byte_info]

def animation_info(value, loop_bit=8, max_frame=253):
    """
    Convert animation info array of two elements to an animation info property.
    The first is 0/1, and defines whether or not the animation loops. The second is the number of frames, at most 253 frames.

    @param value: Array of animation info.
    @type  value: C{Array}

    @param loop_bit: Bit the loop information is stored.
    @type  loop_bit: C{int}

    @param max_frame: Max frames possible.
    @type  max_frame: C{int}

    @return: Value to use for animation property.
    @rtype:  L{Expression}
    """
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("animation_info must be an array with exactly 2 constant values", value.pos)
    looping = value.values[0].reduce_constant().value
    frames  = value.values[1].reduce_constant().value
    if looping not in (0, 1):
        raise generic.ScriptError("First field of the animation_info array must be either 0 or 1", value.values[0].pos)
    if frames < 1 or frames > max_frame:
        raise generic.ScriptError("Second field of the animation_info array must be between 1 and " + str(max_frame), value.values[1].pos)

    return ConstantNumeric((looping << loop_bit) + frames - 1)

def cargo_list(value, max_num_cargos):
    """
    Encode an array of cargo types in a single property value. If less than the maximum
    number of cargos are given the rest is filled up with 0xFF (=invalid cargo).

    @param value: Array of cargo types.
    @type  value: C{Array}

    @param max_num_cargos: The maximum number of cargos in the array.
    @type  max_num_cargos: C{int}

    @param prop_num: Property number.
    @type  prop_num: C{int}

    @param prop_size: Property size in bytes.
    @type  prop_size: C{int}
    """
    if not isinstance(value, Array) or len(value.values) > max_num_cargos:
        raise generic.ScriptError("Cargo list must be an array with no more than %d values" % max_num_cargos, value.pos)
    cargoes = value.values + [ConstantNumeric(0xFF, value.pos) for _ in range(max_num_cargos - len(value.values))]

    ret = None
    for i, cargo in enumerate(cargoes):
        byte = BinOp(nmlop.AND, cargo, ConstantNumeric(0xFF, cargo.pos), cargo.pos)
        if i == 0:
            ret = byte
        else:
            byte = BinOp(nmlop.SHIFT_LEFT, byte, ConstantNumeric(i * 8, cargo.pos), cargo.pos)
            ret = BinOp(nmlop.OR, ret, byte, cargo.pos)
    return ret.reduce()

#
# General vehicle properties that apply to feature 0x00 .. 0x03
#

general_veh_props = {
    'reliability_decay'  : {'size': 1, 'num': 0x02},
    'vehicle_life'       : {'size': 1, 'num': 0x03},
    'model_life'         : {'size': 1, 'num': 0x04},
    'climates_available' : {'size': 1, 'num': 0x06},
    'loading_speed'      : {'size': 1, 'num': 0x07},
    'name'               : {'num': -1, 'string': None},
}

def ottd_display_speed(value, divisor, unit):
    return (value.value / divisor * 10 / 16 * unit.ottd_mul) >> unit.ottd_shift

class CargotypeListProp(BaseAction0Property):
    def __init__(self, prop_num, data):
        # data is a list, each element belongs to an item ID
        # Each element in the list is a list of cargo types
        self.prop_num = prop_num
        self.data = data

    def write(self, file):
        file.print_bytex(self.prop_num)
        for elem in self.data:
            file.print_byte(len(elem))
            for i, val in enumerate(elem):
                if i % 8 == 0: file.newline()
                file.print_bytex(val)
            file.newline()

    def get_size(self):
        total_len = 1 # Prop number
        for elem in self.data:
            # For each item ID to set, make space for all values + 1 for the length
            total_len += len(elem) + 1
        return total_len

def ctt_list(prop_num, *values):
    # values may have multiple entries, if more than one item ID is set (e.g. multitile houses)
    # Each value is an expression.Array of cargo types
    for value in values:
        if not isinstance(value, Array):
            raise generic.ScriptError("Value of cargolist property must be an array", value.pos)
    return [CargotypeListProp(prop_num, [[ctype.reduce_constant().value for ctype in single_item_array.values] for single_item_array in values])]

def vehicle_length(value):
    if isinstance(value, ConstantNumeric):
        generic.check_range(value.value, 1, 8, "vehicle length", value.pos)
    return BinOp(nmlop.SUB, ConstantNumeric(8, value.pos), value, value.pos).reduce()

def zero_refit_mask(prop_num):
    # Zero the refit mask, in addition to setting some other refit property
    return {'size': 4, 'num': prop_num, 'value_function': lambda value: ConstantNumeric(0)}
#
# Feature 0x00 (Trains)
#

properties[0x00] = {
    'track_type'                   : {'size': 1, 'num': 0x05},
    'ai_special_flag'              : {'size': 1, 'num': 0x08},
    'speed'                        : {'size': 2, 'num': 0x09, 'unit_type': 'speed', 'unit_conversion': (5000, 1397), 'adjust_value': lambda val, unit: ottd_display_speed(val, 1, unit)},
    # 09 doesn't exist
    'power'                        : {'size': 2, 'num': 0x0B, 'unit_type': 'power'},
    # 0A doesn't exist
    'running_cost_factor'          : {'size': 1, 'num': 0x0D},
    'running_cost_base'            : {'size': 4, 'num': 0x0E},
    # 0F -11 don't exist
    'sprite_id'                    : {'size': 1, 'num': 0x12},
    'dual_headed'                  : {'size': 1, 'num': 0x13},
    'cargo_capacity'               : {'size': 1, 'num': 0x14},
    'default_cargo_type'           : {'size': 1, 'num': 0x15},
    'weight'                       : two_byte_property(0x16, 0x24, {'unit_type': 'weight'}, {'unit_type': 'weight'}),
    'cost_factor'                  : {'size': 1, 'num': 0x17},
    'ai_engine_rank'               : {'size': 1, 'num': 0x18},
    'engine_class'                 : {'size': 1, 'num': 0x19},
    # 1A (sort purchase list) is implemented elsewhere
    'extra_power_per_wagon'        : {'size': 2, 'num': 0x1B, 'unit_type': 'power'},
    'refit_cost'                   : {'size': 1, 'num': 0x1C},
    # 1D (refittable cargo types) is removed, it is zeroed when setting a different refit property
    # 1E (callback flags) is not set by user
    'tractive_effort_coefficient'  : {'size': 1, 'num': 0x1F, 'unit_conversion': 255},
    'air_drag_coefficient'         : {'size': 1, 'num': 0x20, 'unit_conversion': 255},
    'length'                       : {'size': 1, 'num': 0x21, 'value_function': vehicle_length},
    'visual_effect_and_powered'    : {'size': 1, 'num': 0x22},
    'extra_weight_per_wagon'       : {'size': 1, 'num': 0x23, 'unit_type': 'weight'},
    # 24 is high byte of 16 (weight)
    'bitmask_vehicle_info'         : {'size': 1, 'num': 0x25},
    'retire_early'                 : {'size': 1, 'num': 0x26},
    'misc_flags'                   : {'size': 1, 'num': 0x27},
    'refittable_cargo_classes'     : [{'size': 2, 'num': 0x28}, zero_refit_mask(0x1D)],
    'non_refittable_cargo_classes' : [{'size': 2, 'num': 0x29}, zero_refit_mask(0x1D)],
    'introduction_date'            : {'size': 4, 'num': 0x2A},
    'cargo_age_period'             : {'size': 2, 'num': 0x2B},
    'cargo_allow_refit'            : [{'custom_function': lambda value: ctt_list(0x2C, value)}, zero_refit_mask(0x1D)],
    'cargo_disallow_refit'         : [{'custom_function': lambda value: ctt_list(0x2D, value)}, zero_refit_mask(0x1D)],
}
properties[0x00].update(general_veh_props)

#
# Feature 0x01 (Road Vehicles)
#

def roadveh_speed_prop(prop_info):
    # prop 08 value is min(value, 255)
    prop08_value = lambda value: BinOp(nmlop.MIN, value, ConstantNumeric(0xFF, value.pos), value.pos).reduce()
    # prop 15 value is (value + 3) / 4
    prop15_value = lambda value: BinOp(nmlop.DIV, BinOp(nmlop.ADD, value, ConstantNumeric(3, value.pos), value.pos), ConstantNumeric(4, value.pos), value.pos).reduce()
    # prop 15 should not be set if value <= 255
    prop15_test = lambda value: not (isinstance(value, ConstantNumeric) and value.value <= 0xFF)
    prop08 = {'size': 1, 'num': 0x08, 'value_function': prop08_value}
    prop15 = {'size': 1, 'num': 0x15, 'value_function': prop15_value, 'test_function': prop15_test}
    for key in prop_info:
        prop08[key] = prop15[key] = prop_info[key]
    return [prop08, prop15]

properties[0x01] = {
    'speed'                        : roadveh_speed_prop({'unit_type': 'speed', 'unit_conversion': (10000, 1397), 'adjust_value': lambda val, unit: ottd_display_speed(val, 2, unit)}),
    'running_cost_factor'          : {'size': 1, 'num': 0x09},
    'running_cost_base'            : {'size': 4, 'num': 0x0A},
    # 0B -0D don't exist
    'sprite_id'                    : {'size': 1, 'num': 0x0E},
    'cargo_capacity'               : {'size': 1, 'num': 0x0F},
    'default_cargo_type'           : {'size': 1, 'num': 0x10},
    'cost_factor'                  : {'size': 1, 'num': 0x11},
    'sound_effect'                 : {'size': 1, 'num': 0x12},
    'power'                        : {'size': 1, 'num': 0x13, 'unit_type': 'power', 'unit_conversion': (1, 10)},
    'weight'                       : {'size': 1, 'num': 0x14, 'unit_type': 'weight', 'unit_conversion': 4},
    # 15 is set together with 08 (see above)
    # 16 (refittable cargo types) is removed, it is zeroed when setting a different refit property
    # 17 (callback flags) is not set by user
    'tractive_effort_coefficient'  : {'size': 1, 'num': 0x18, 'unit_conversion': 255},
    'air_drag_coefficient'         : {'size': 1, 'num': 0x19, 'unit_conversion': 255},
    'refit_cost'                   : {'size': 1, 'num': 0x1A},
    'retire_early'                 : {'size': 1, 'num': 0x1B},
    'misc_flags'                   : {'size': 1, 'num': 0x1C},
    'refittable_cargo_classes'     : [{'size': 2, 'num': 0x1D}, zero_refit_mask(0x16)],
    'non_refittable_cargo_classes' : [{'size': 2, 'num': 0x1E}, zero_refit_mask(0x16)],
    'introduction_date'            : {'size': 4, 'num': 0x1F},
    # 20 (sort purchase list) is implemented elsewhere
    'visual_effect'                : {'size': 1, 'num': 0x21},
    'cargo_age_period'             : {'size': 2, 'num': 0x22},
    'length'                       : {'size': 1, 'num': 0x23, 'value_function': vehicle_length},
    'cargo_allow_refit'            : [{'custom_function': lambda value: ctt_list(0x24, value)}, zero_refit_mask(0x16)],
    'cargo_disallow_refit'         : [{'custom_function': lambda value: ctt_list(0x25, value)}, zero_refit_mask(0x16)],
}
properties[0x01].update(general_veh_props)

#
# Feature 0x02 (Ships)
#

def speed_fraction(value):
    # Unit is already converted to 0 .. 255 range when we get here
    if isinstance(value, ConstantNumeric) and not (0 <= value.value <= 255):
        # Do not use check_range to provide better error message
        raise generic.ScriptError("speed fraction must be in range 0 .. 1", value.pos)
    return BinOp(nmlop.SUB, ConstantNumeric(255, value.pos), value, value.pos).reduce()

properties[0x02] = {
    'sprite_id'                    : {'size': 1, 'num': 0x08},
    'is_refittable'                : {'size': 1, 'num': 0x09},
    'cost_factor'                  : {'size': 1, 'num': 0x0A},
    'speed'                        : {'size': 1, 'num': 0x0B, 'unit_type': 'speed', 'unit_conversion': (10000, 1397), 'adjust_value': lambda val, unit: ottd_display_speed(val, 2, unit)},
    'default_cargo_type'           : {'size': 1, 'num': 0x0C},
    'cargo_capacity'               : {'size': 2, 'num': 0x0D},
    # 0E does not exist
    'running_cost_factor'          : {'size': 1, 'num': 0x0F},
    'sound_effect'                 : {'size': 1, 'num': 0x10},
    # 11 (refittable cargo types) is removed, it is zeroed when setting a different refit property
    # 12 (callback flags) is not set by user
    'refit_cost'                   : {'size': 1, 'num': 0x13},
    'ocean_speed_fraction'         : {'size': 1, 'num': 0x14, 'unit_conversion': 255, 'value_function': speed_fraction},
    'canal_speed_fraction'         : {'size': 1, 'num': 0x15, 'unit_conversion': 255, 'value_function': speed_fraction},
    'retire_early'                 : {'size': 1, 'num': 0x16},
    'misc_flags'                   : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes'     : [{'size': 2, 'num': 0x18}, zero_refit_mask(0x11)],
    'non_refittable_cargo_classes' : [{'size': 2, 'num': 0x19}, zero_refit_mask(0x11)],
    'introduction_date'            : {'size': 4, 'num': 0x1A},
    # 1B (sort purchase list) is implemented elsewhere
    'visual_effect'                : {'size': 1, 'num': 0x1C},
    'cargo_age_period'             : {'size': 2, 'num': 0x1D},
    'cargo_allow_refit'            : [{'custom_function': lambda value: ctt_list(0x1E, value)}, zero_refit_mask(0x11)],
    'cargo_disallow_refit'         : [{'custom_function': lambda value: ctt_list(0x1F, value)}, zero_refit_mask(0x11)],
}
properties[0x02].update(general_veh_props)

#
# Feature 0x03 (Aircraft)
#

def aircraft_is_heli(value):
    if isinstance(value, ConstantNumeric) and not value.value in (0, 2, 3):
        raise generic.ScriptError("Invalid value for aircraft_type", value.pos)
    return BinOp(nmlop.AND, value, ConstantNumeric(2, value.pos), value.pos).reduce()

def aircraft_is_large(value):
    return BinOp(nmlop.AND, value, ConstantNumeric(1, value.pos), value.pos).reduce()

properties[0x03] = {
    'sprite_id'                    : {'size': 1, 'num': 0x08},
    'aircraft_type'                : [{'size': 1, 'num': 0x09, 'value_function': aircraft_is_heli}, {'size': 1, 'num': 0x0A, 'value_function': aircraft_is_large}],
    'cost_factor'                  : {'size': 1, 'num': 0x0B},
    'speed'                        : {'size': 1, 'num': 0x0C, 'unit_type': 'speed', 'unit_conversion': (701, 2507), 'adjust_value': lambda val, unit: ottd_display_speed(val, 1, unit)},
    'acceleration'                 : {'size': 1, 'num': 0x0D},
    'running_cost_factor'          : {'size': 1, 'num': 0x0E},
    'passenger_capacity'           : {'size': 2, 'num': 0x0F},
    # 10 does not exist
    'mail_capacity'                : {'size': 1, 'num': 0x11},
    'sound_effect'                 : {'size': 1, 'num': 0x12},
    # 13 (refittable cargo types) is removed, it is zeroed when setting a different refit property
    # 14 (callback flags) is not set by user
    'refit_cost'                   : {'size': 1, 'num': 0x15},
    'retire_early'                 : {'size': 1, 'num': 0x16},
    'misc_flags'                   : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes'     : [{'size': 2, 'num': 0x18}, zero_refit_mask(0x13)],
    'non_refittable_cargo_classes' : [{'size': 2, 'num': 0x19}, zero_refit_mask(0x13)],
    'introduction_date'            : {'size': 4, 'num': 0x1A},
    # 1B (sort purchase list) is implemented elsewhere
    'cargo_age_period'             : {'size': 2, 'num': 0x1C},
    'cargo_allow_refit'            : [{'custom_function': lambda value: ctt_list(0x1D, value)}, zero_refit_mask(0x13)],
    'cargo_disallow_refit'         : [{'custom_function': lambda value: ctt_list(0x1E, value)}, zero_refit_mask(0x13)],
    'range'                        : {'size': 2, 'num': 0x1F},
}
properties[0x03].update(general_veh_props)

# TODO: Feature 0x04

#
# Feature 0x05 (Canals)
#

properties[0x05] = {
    # 08 (callback flags) not set by user
    'graphic_flags'  : {'size': 1, 'num': 0x09},
}

# TODO: Feature 0x06

#
# Feature 0x07 (Houses)
#

def house_prop_0A(value):
    # User sets an array [min_year, max_year] as property value
    # House property 0A is set to ((max_year - 1920) << 8) | (min_year - 1920)
    # With both bytes clamped to the 0 .. 255 range
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Availability years must be an array with exactly two values", value.pos)

    min_year = BinOp(nmlop.SUB, value.values[0], ConstantNumeric(1920, value.pos), value.pos)
    min_year = BinOp(nmlop.MAX, min_year, ConstantNumeric(0, value.pos), value.pos)
    min_year = BinOp(nmlop.MIN, min_year, ConstantNumeric(255, value.pos), value.pos)

    max_year = BinOp(nmlop.SUB, value.values[1], ConstantNumeric(1920, value.pos), value.pos)
    max_year = BinOp(nmlop.MAX, max_year, ConstantNumeric(0, value.pos), value.pos)
    max_year = BinOp(nmlop.MIN, max_year, ConstantNumeric(255, value.pos), value.pos)
    max_year = BinOp(nmlop.SHIFT_LEFT, max_year, ConstantNumeric(8, value.pos), value.pos)

    return BinOp(nmlop.OR, max_year, min_year, value.pos).reduce()

def house_prop_21_22(value, index):
    # Take one of the values from the years_available array
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Availability years must be an array with exactly two values", value.pos)
    return value.values[index]

def house_acceptance(value, index):
    if not isinstance(value, Array) or len(value.values) > 3:
        raise generic.ScriptError("accepted_cargos must be an array with no more than 3 values", value.pos)

    if index < len(value.values):
        cargo_amount_pair = value.values[index]
        if not isinstance(cargo_amount_pair, Array) or len(cargo_amount_pair.values) != 2:
            raise generic.ScriptError("Each element of accepted_cargos must be an array with two elements: cargoid and amount", cargo_amount_pair.pos)
        return cargo_amount_pair.values[1]
    else:
        return ConstantNumeric(0, value.pos)

def house_accepted_cargo_types(value):
    if not isinstance(value, Array) or len(value.values) > 3:
        raise generic.ScriptError("accepted_cargos must be an array with no more than 3 values", value.pos)

    cargoes = []
    for i in range(3):
        if i < len(value.values):
            cargo_amount_pair = value.values[i]
            if not isinstance(cargo_amount_pair, Array) or len(cargo_amount_pair.values) != 2:
                raise generic.ScriptError("Each element of accepted_cargos must be an array with two elements: cargoid and amount", cargo_amount_pair.pos)
            cargoes.append(cargo_amount_pair.values[0])
        else:
            cargoes.append(ConstantNumeric(0xFF, value.pos))

    ret = None
    for i, cargo in enumerate(cargoes):
        byte = BinOp(nmlop.AND, cargo, ConstantNumeric(0xFF, cargo.pos), cargo.pos)
        if i == 0:
            ret = byte
        else:
            byte = BinOp(nmlop.SHIFT_LEFT, byte, ConstantNumeric(i * 8, cargo.pos), cargo.pos)
            ret = BinOp(nmlop.OR, ret, byte, cargo.pos)
    return ret.reduce()

def house_random_colours(value):
    # User sets array with 4 values (range 0..15)
    # Output is a dword, each byte being a value from the array
    if not isinstance(value, Array) or len(value.values) != 4:
        raise generic.ScriptError("Random colours must be an array with exactly four values", value.pos)

    ret = None
    for i, colour in enumerate(value.values):
        if isinstance(colour, ConstantNumeric):
            generic.check_range(colour.value, 0, 15, "Random house colours", colour.pos)
        byte = BinOp(nmlop.AND, colour, ConstantNumeric(0xFF, colour.pos), colour.pos)
        if i == 0:
            ret = byte
        else:
            byte = BinOp(nmlop.SHIFT_LEFT, byte, ConstantNumeric(i * 8, colour.pos), colour.pos)
            ret = BinOp(nmlop.OR, ret, byte, colour.pos)
    return ret.reduce()

    return [Action0Property(0x17, ConstantNumeric(colours[0] << 24 | colours[1] << 16 | colours[2] << 8 | colours[3]), 4)]

def house_available_mask(value):
    # User sets [town_zones, climates] array
    # Which is mapped to (town_zones | (climates & 0x800) | ((climates & 0xF) << 12))
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("availability_mask must be an array with exactly 2 values", value.pos)\

    climates = BinOp(nmlop.AND, value.values[1], ConstantNumeric(0xF, value.pos), value.pos)
    climates = BinOp(nmlop.SHIFT_LEFT, climates, ConstantNumeric(12, value.pos), value.pos)
    above_snow = BinOp(nmlop.AND, value.values[1], ConstantNumeric(0x800, value.pos), value.pos)

    ret = BinOp(nmlop.OR, climates, value.values[0], value.pos)
    ret = BinOp(nmlop.OR, ret, above_snow, value.pos)
    return ret.reduce()

# List of valid IDs of old house types
old_houses = {
0 : set(), # 1x1, see below
2 : set([74, 76, 87]), # 2x1
3 : set([7, 66, 68, 99]), # 1x2
4 : set([20, 32, 40]), # 2x2
}
# All houses not part of a multitile-house, are 1x1 houses
old_houses[0] = set(range(110)).difference( house + i for house in (itertools.chain(*old_houses.values())) for i in range(4 if house in old_houses[4] else 2) )

def mt_house_old_id(value, num_ids, size_bit):
    # For substitute / override properties
    # Set value for tile i (0 .. 3) to (value + i)
    # Also validate that the size of the old house matches
    if isinstance(value, ConstantNumeric) and not value.value in old_houses[size_bit]:
        raise generic.ScriptError("Substitute / override house type must have the same size as the newly defined house.", value.pos)
    ret = [value]
    for i in range(1, num_ids):
        ret.append(BinOp(nmlop.ADD, value, ConstantNumeric(i, value.pos), value.pos).reduce())
    return ret

def mt_house_prop09(value, num_ids, size_bit):
    # Only bit 5 should be set for additional tiles
    # Additionally, correctly set the size bit (0, 2, 3 or 4) for the first tile
    if isinstance(value, ConstantNumeric) and (value.value & 0x1D) != 0:
        raise generic.ScriptError("Invalid bits set in house property 'building_flags'.", value.pos)
    ret = [BinOp(nmlop.OR, value, ConstantNumeric(1 << size_bit, value.pos), value.pos).reduce()]
    for i in range(1, num_ids):
        ret.append(BinOp(nmlop.AND, value, ConstantNumeric(1 << 5, value.pos), value.pos).reduce())
    return ret

def mt_house_mask(mask, value, num_ids, size_bit):
    # Mask out the bits not present in the 'mask' parameter for additional tiles
    ret = [value]
    for i in range(1, num_ids):
        ret.append(BinOp(nmlop.AND, value, ConstantNumeric(mask, value.pos), value.pos).reduce())
    return ret

def mt_house_zero(value, num_ids, size_bit):
    return [value] + (num_ids - 1) * [ConstantNumeric(0, value.pos)]

def mt_house_same(value, num_ids, size_bit):
    # Set to the same value for all tiles
    return num_ids * [value]

def mt_house_class(value, num_ids, size_bit):
    # Set class to 0xFF for additional tiles
    return [value] + (num_ids - 1) * [ConstantNumeric(0xFF, value.pos)]

properties[0x07] = {
    'substitute'              : {'size': 1, 'num': 0x08, 'multitile_function': mt_house_old_id, 'first': None},
    'building_flags'          : two_byte_property(0x09, 0x19, {'multitile_function': mt_house_prop09}, {'multitile_function': lambda *args: mt_house_mask(0xFE, *args)}),
    'years_available'         : [{'size': 2, 'num': 0x0A, 'multitile_function': mt_house_zero, 'value_function': house_prop_0A},
                                 {'size': 2, 'num': 0x21, 'multitile_function': mt_house_zero, 'value_function': lambda value: house_prop_21_22(value, 0)},
                                 {'size': 2, 'num': 0x22, 'multitile_function': mt_house_zero, 'value_function': lambda value: house_prop_21_22(value, 1)}],
    'population'              : {'size': 1, 'num': 0x0B, 'multitile_function': mt_house_zero},
    'mail_multiplier'         : {'size': 1, 'num': 0x0C, 'multitile_function': mt_house_zero},
    'accepted_cargos'         : [{'size': 1, 'num': 0x0D, 'multitile_function': mt_house_same, 'value_function': lambda value: house_acceptance(value, 0)},
                                 {'size': 1, 'num': 0x0E, 'multitile_function': mt_house_same, 'value_function': lambda value: house_acceptance(value, 1)},
                                 {'size': 1, 'num': 0x0F, 'multitile_function': mt_house_same, 'value_function': lambda value: house_acceptance(value, 2)},
                                 {'size': 4, 'num': 0x1E, 'multitile_function': mt_house_same, 'value_function': house_accepted_cargo_types}],
    'local_authority_impact'  : {'size': 2, 'num': 0x10, 'multitile_function': mt_house_same},
    'removal_cost_multiplier' : {'size': 1, 'num': 0x11, 'multitile_function': mt_house_same},
    'name'                    : {'size': 2, 'num': 0x12, 'string': 0xDC, 'multitile_function': mt_house_same},
    'availability_mask'       : {'size': 2, 'num': 0x13, 'multitile_function': mt_house_zero, 'value_function': house_available_mask},
    # prop 14 (callback flags 1) is not set by user
    'override'                : {'size': 1, 'num': 0x15, 'multitile_function': mt_house_old_id},
    'refresh_multiplier'      : {'size': 1, 'num': 0x16, 'multitile_function': mt_house_same},
    'random_colours'          : {'size': 4, 'num': 0x17, 'multitile_function': mt_house_same, 'value_function': house_random_colours},
    'probability'             : {'size': 1, 'num': 0x18, 'multitile_function': mt_house_zero, 'unit_conversion': 16},
    # prop 19 is the high byte of prop 09
    'animation_info'          : {'size': 1, 'num': 0x1A, 'multitile_function': mt_house_same, 'value_function': lambda value: animation_info(value, 7, 128)},
    'animation_speed'         : {'size': 1, 'num': 0x1B, 'multitile_function': mt_house_same},
    'building_class'          : {'size': 1, 'num': 0x1C, 'multitile_function': mt_house_class},
    # prop 1D (callback flags 2) is not set by user
    'minimum_lifetime'        : {'size': 1, 'num': 0x1F, 'multitile_function': mt_house_zero},
    'watched_cargo_types'     : {'multitile_function': mt_house_same, 'custom_function': lambda *values: ctt_list(0x20, *values)}
    # prop 21 -22 see above (years_available, prop 0A)
}

# Feature 0x08 (General Vars) is implemented elsewhere (e.g. basecost, snowline)

#
# Feature 0x09 (Industry Tiles)
#

def industrytile_cargos(value):
    if not isinstance(value, Array) or len(value.values) > 3:
        raise generic.ScriptError("accepted_cargos must be an array with no more than 3 values", value.pos)
    prop_num = 0x0A
    props = []
    for cargo_amount_pair in value.values:
        if not isinstance(cargo_amount_pair, Array) or len(cargo_amount_pair.values) != 2:
            raise generic.ScriptError("Each element of accepted_cargos must be an array with two elements: cargoid and amount", cargo_amount_pair.pos)
        cargo_id = cargo_amount_pair.values[0].reduce_constant().value
        cargo_amount = cargo_amount_pair.values[1].reduce_constant().value
        props.append(Action0Property(prop_num, ConstantNumeric((cargo_amount << 8) | cargo_id), 2))
        prop_num += 1

    while prop_num <= 0x0C:
        props.append(Action0Property(prop_num, ConstantNumeric(0), 2))
        prop_num += 1
    return props

properties[0x09] = {
    'substitute'         : {'size': 1, 'num': 0x08, 'first': None},
    'override'           : {'size': 1, 'num': 0x09},
    'accepted_cargos'    : {'custom_function': industrytile_cargos}, # = prop 0A - 0C
    'land_shape_flags'   : {'size': 1, 'num': 0x0D},
    # prop 0E (callback flags) is not set by user
    'animation_info'     : {'size': 2, 'num': 0x0F, 'value_function': animation_info},
    'animation_speed'    : {'size': 1, 'num': 0x10},
    'animation_triggers' : {'size': 1, 'num': 0x11},
    'special_flags'      : {'size': 1, 'num': 0x12},
}

#
# Feature 0x0A (Industries)
#

class IndustryLayoutProp(BaseAction0Property):
    def __init__(self, layout_list):
        self.layout_list = layout_list

    def write(self, file):
        file.print_bytex(0x0A)
        file.print_byte(len(self.layout_list))
        # -6 because prop_num, num_layouts and size should not be included
        file.print_dword(self.get_size() - 6)
        file.newline()
        for layout in self.layout_list:
            layout.write(file)
        file.newline()

    def get_size(self):
        size = 6
        for layout in self.layout_list:
            size += layout.get_size()
        return size

def industry_layouts(value):
    if not isinstance(value, Array) or not all(map(lambda x: isinstance(x, Identifier), value.values)):
        raise generic.ScriptError("layouts must be an array of layout names", value.pos)
    layouts = []
    for name in value.values:
        if name.value not in tilelayout_names:
            raise generic.ScriptError("Unknown layout name '%s'" % name.value, name.pos)
        layouts.append(tilelayout_names[name.value])
    return [IndustryLayoutProp(layouts)]

def industry_prod_multiplier(value):
    if not isinstance(value, Array) or len(value.values) > 2:
        raise generic.ScriptError("Prod multiplier must be an array of up to two values", value.pos)
    props = []
    for i in range(0, 2):
        val = value.values[i].reduce_constant() if i < len(value.values) else ConstantNumeric(0)
        props.append(Action0Property(0x12 + i, val, 1))
    return props

class RandomSoundsProp(BaseAction0Property):
    def __init__(self, sound_list):
        self.sound_list = sound_list

    def write(self, file):
        file.print_bytex(0x15)
        file.print_byte(len(self.sound_list))
        for sound in self.sound_list:
            sound.write(file, 1)
        file.newline()

    def get_size(self):
        return len(self.sound_list) + 2

def random_sounds(value):
    if not isinstance(value, Array) or not all(map(lambda x: isinstance(x, ConstantNumeric), value.values)):
        raise generic.ScriptError("random_sound_effects must be an array with sounds effects", value.pos)
    return [RandomSoundsProp(value.values)]

class ConflictingTypesProp(BaseAction0Property):
    def __init__(self, types_list):
        self.types_list = types_list
        assert len(self.types_list) == 3

    def write(self, file):
        file.print_bytex(0x16)
        for type in self.types_list:
            type.write(file, 1)
        file.newline()

    def get_size(self):
        return len(self.types_list) + 1

def industry_conflicting_types(value):
    if not isinstance(value, Array):
        raise generic.ScriptError("conflicting_ind_types must be an array of industry types", value.pos)
    if len(value.values) > 3:
        raise generic.ScriptError("conflicting_ind_types may have at most three entries", value.pos)

    types_list = []
    for val in value.values:
        types_list.append(val.reduce_constant())
    while len(types_list) < 3:
        types_list.append(ConstantNumeric(0xFF))
    return [ConflictingTypesProp(types_list)]

def industry_input_multiplier(value, prop_num):
    if not isinstance(value, Array) or len(value.values) > 2:
        raise generic.ScriptError("Input multiplier must be an array of up to two values", value.pos)
    val1 = value.values[0].reduce() if len(value.values) > 0 else ConstantNumeric(0)
    val2 = value.values[1].reduce() if len(value.values) > 1 else ConstantNumeric(0)
    if not isinstance(val1, (ConstantNumeric, ConstantFloat)) or not isinstance(val2, (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Expected a compile-time constant", value.pos)
    generic.check_range(val1.value, 0, 256, "input_multiplier", val1.pos)
    generic.check_range(val2.value, 0, 256, "input_multiplier", val2.pos)
    mul1 = int(val1.value * 256)
    mul2 = int(val2.value * 256)
    return [Action0Property(prop_num, ConstantNumeric(mul1 | (mul2 << 16)), 4)]

properties[0x0A] = {
    'substitute'             : {'size': 1, 'num': 0x08, 'first': None},
    'override'               : {'size': 1, 'num': 0x09},
    'layouts'                : {'custom_function': industry_layouts}, # = prop 0A
    'life_type'              : {'size': 1, 'num': 0x0B},
    'closure_msg'            : {'size': 2, 'num': 0x0C, 'string': 0xDC},
    'prod_increase_msg'      : {'size': 2, 'num': 0x0D, 'string': 0xDC},
    'prod_decrease_msg'      : {'size': 2, 'num': 0x0E, 'string': 0xDC},
    'fund_cost_multiplier'   : {'size': 1, 'num': 0x0F},
    'prod_cargo_types'       : {'size': 2, 'num': 0x10, 'value_function': lambda value: cargo_list(value, 2)},
    'accept_cargo_types'     : {'size': 4, 'num': 0x11, 'value_function': lambda value: cargo_list(value, 3)},
    'prod_multiplier'        : {'custom_function': industry_prod_multiplier}, # = prop 12,13
    'min_cargo_distr'        : {'size': 1, 'num': 0x14},
    'random_sound_effects'   : {'custom_function': random_sounds}, # = prop 15
    'conflicting_ind_types'  : {'custom_function': industry_conflicting_types}, # = prop 16
    'prob_random'            : {'size': 1, 'num': 0x17},
    'prob_in_game'           : {'size': 1, 'num': 0x18},
    'map_colour'             : {'size': 1, 'num': 0x19},
    'spec_flags'             : {'size': 4, 'num': 0x1A},
    'new_ind_msg'            : {'size': 2, 'num': 0x1B, 'string': 0xDC},
    'input_multiplier_1'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1C)},
    'input_multiplier_2'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1D)},
    'input_multiplier_3'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1E)},
    'name'                   : {'size': 2, 'num': 0x1F, 'string': 0xDC},
    'prospect_chance'        : {'size': 4, 'num': 0x20, 'unit_conversion': 0xFFFFFFFF},
    # prop 21, 22 (callback flags) are not set by user
    'remove_cost_multiplier' : {'size': 4, 'num': 0x23},
    'nearby_station_name'    : {'size': 2, 'num': 0x24, 'string': 0xDC},
}

#
# Feature 0x0B (Cargos)
#

properties[0x0B] = {
    'number'                    : {'num' : 0x08, 'size' : 1},
    'type_name'                 : {'num' : 0x09, 'size' : 2, 'string' : 0xDC},
    'unit_name'                 : {'num' : 0x0A, 'size' : 2, 'string' : 0xDC},
    # Properties 0B, 0C are not used by OpenTTD
    'type_abbreviation'         : {'num' : 0x0D, 'size' : 2, 'string' : 0xDC},
    'sprite'                    : {'num' : 0x0E, 'size' : 2},
    'weight'                    : {'num' : 0x0F, 'size' : 1, 'unit_type' : 'weight', 'unit_conversion' : 16},
    'penalty_lowerbound'        : {'num' : 0x10, 'size' : 1},
    'single_penalty_length'     : {'num' : 0x11, 'size' : 1},
    'price_factor'              : {'num' : 0x12, 'size' : 4, 'unit_conversion' : (1 << 21, 10 * 20 * 255)}, # 10 units of cargo across 20 tiles, with time factor = 255
    'station_list_colour'       : {'num' : 0x13, 'size' : 1},
    'cargo_payment_list_colour' : {'num' : 0x14, 'size' : 1},
    'is_freight'                : {'num' : 0x15, 'size' : 1},
    'cargo_classes'             : {'num' : 0x16, 'size' : 2},
    'cargo_label'               : {'num' : 0x17, 'size' : 4, 'string_literal': 4},
    'town_growth_effect'        : {'num' : 0x18, 'size' : 1},
    'town_growth_multiplier'    : {'num' : 0x19, 'size' : 2, 'unit_conversion' : 0x100},
    # 1A (callback flags) is not set by user
    'units_of_cargo'            : {'num' : 0x1B, 'size' : 2, 'string' : 0xDC},
    'items_of_cargo'            : {'num' : 0x1C, 'size' : 2, 'string' : 0xDC},
    'capacity_multiplier'       : {'num' : 0x1D, 'size' : 2, 'unit_conversion' : 0x100},
}

# Feature 0x0C (Sound Effects) is implemented differently

#
# Feature 0x0D (Airports)
#

def airport_years(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Availability years must be an array with exactly two values", value.pos)
    min_year = value.values[0].reduce_constant()
    max_year = value.values[1].reduce_constant()
    return [Action0Property(0x0C, ConstantNumeric(max_year.value << 16 | min_year.value), 4)]

class AirportLayoutProp(BaseAction0Property):
    def __init__(self, layout_list):
        self.layout_list = layout_list

    def write(self, file):
        file.print_bytex(0x0A)
        file.print_byte(len(self.layout_list))
        # -6 because prop_num, num_layouts and size should not be included
        file.print_dword(self.get_size() - 6)
        file.newline()
        for layout in self.layout_list:
            file.print_bytex(layout.properties['rotation'].value)
            layout.write(file)
        file.newline()

    def get_size(self):
        size = 6
        for layout in self.layout_list:
            size += layout.get_size() + 1
        return size

def airport_layouts(value):
    if not isinstance(value, Array) or not all(map(lambda x: isinstance(x, Identifier), value.values)):
        raise generic.ScriptError("layouts must be an array of layout names", value.pos)
    layouts = []
    for name in value.values:
        if name.value not in tilelayout_names:
            raise generic.ScriptError("Unknown layout name '%s'" % name.value, name.pos)
        layout = tilelayout_names[name.value]
        if 'rotation' not in layout.properties:
            raise generic.ScriptError("Airport layouts must have the 'rotation' property", layout.pos)
        if layout.properties['rotation'].value not in (0, 2, 4, 6):
            raise generic.ScriptError("Airport layout rotation is not a valid direction.", layout.properties['rotation'].pos)
        layouts.append(layout)
    return [AirportLayoutProp(layouts)]

properties[0x0D] = {
    'override'         : {'size': 1, 'num': 0x08, 'first':None},
    # 09 does not exist
    'layouts'          : {'custom_function': airport_layouts}, # = prop 0A
    # 0B does not exist
    'years_available'  : {'custom_function': airport_years}, # = prop 0C
    'ttd_airport_type' : {'size': 1, 'num': 0x0D},
    'catchment_area'   : {'size': 1, 'num': 0x0E},
    'noise_level'      : {'size': 1, 'num': 0x0F},
    'name'             : {'size': 2, 'num': 0x10, 'string': 0xDC},
    'maintenance_cost' : {'size': 2, 'num': 0x11},
}

# Feature 0x0E (Signals) doesn't currently have any action0

#
# Feature 0x0F (Objects)
#

def object_size(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Object size must be an array with exactly two values", value.pos)
    sizex = value.values[0].reduce_constant()
    sizey = value.values[1].reduce_constant()
    if sizex.value < 1 or sizex.value > 15 or sizey.value < 1 or sizey.value > 15:
        raise generic.ScriptError("The size of an object must be at least 1x1 and at most 15x15 tiles", value.pos)
    return [Action0Property(0x0C, ConstantNumeric(sizey.value << 4 | sizex.value), 1)]

properties[0x0F] = {
    'class'                  : {'size': 4, 'num': 0x08, 'first': None, 'string_literal': 4},
    # strings might be according to specs be either 0xD0 or 0xD4
    'classname'              : {'size': 2, 'num': 0x09, 'string': 0xD0},
    'name'                   : {'size': 2, 'num': 0x0A, 'string': 0xD0},
    'climates_available'     : {'size': 1, 'num': 0x0B},
    'size'                   : {'custom_function': object_size}, # = prop 0C
    'build_cost_multiplier'  : {'size': 1, 'num': 0x0D},
    'introduction_date'      : {'size': 4, 'num': 0x0E},
    'end_of_life_date'       : {'size': 4, 'num': 0x0F},
    'object_flags'           : {'size': 2, 'num': 0x10},
    'animation_info'         : {'size': 2, 'num': 0x11, 'value_function': animation_info},
    'animation_speed'        : {'size': 1, 'num': 0x12},
    'animation_triggers'     : {'size': 2, 'num': 0x13},
    'remove_cost_multiplier' : {'size': 1, 'num': 0x14},
    # 15 (callback flags) is not set by user
    'height'                 : {'size': 1, 'num': 0x16},
    'num_views'              : {'size': 1, 'num': 0x17},
}

#
# Feature 0x10 (Rail Types)
#

class RailtypeListProp(BaseAction0Property):
    def __init__(self, prop_num, railtype_list):
        self.prop_num = prop_num
        self.railtype_list = railtype_list

    def write(self, file):
        file.print_bytex(self.prop_num)
        file.print_byte(len(self.railtype_list))
        for railtype in self.railtype_list:
            railtype.write(file, 4)
        file.newline()

    def get_size(self):
        return len(self.railtype_list) * 4 + 2

def railtype_list(value, prop_num):
    if not isinstance(value, Array):
        raise generic.ScriptError("Railtype list must be an array of literal strings", value.pos)
    for val in value.values:
        if not isinstance(val, StringLiteral): raise generic.ScriptError("Railtype list must be an array of literal strings", val.pos)
    return [RailtypeListProp(prop_num, value.values)]

properties[0x10] = {
    'label'                    : {'size': 4, 'num': 0x08, 'string_literal': 4}, # is allocated during reservation stage, setting label first is thus not needed
    'toolbar_caption'          : {'size': 2, 'num': 0x09, 'string': 0xDC},
    'menu_text'                : {'size': 2, 'num': 0x0A, 'string': 0xDC},
    'build_window_caption'     : {'size': 2, 'num': 0x0B, 'string': 0xDC},
    'autoreplace_text'         : {'size': 2, 'num': 0x0C, 'string': 0xDC},
    'new_engine_text'          : {'size': 2, 'num': 0x0D, 'string': 0xDC},
    'compatible_railtype_list' : {'custom_function': lambda x: railtype_list(x, 0x0E)},
    'powered_railtype_list'    : {'custom_function': lambda x: railtype_list(x, 0x0F)},
    'railtype_flags'           : {'size': 1, 'num': 0x10},
    'curve_speed_multiplier'   : {'size': 1, 'num': 0x11},
    'station_graphics'         : {'size': 1, 'num': 0x12},
    'construction_cost'        : {'size': 2, 'num': 0x13},
    'speed_limit'              : {'size': 2, 'num': 0x14, 'unit_type': 'speed', 'unit_conversion': (5000, 1397)},
    'acceleration_model'       : {'size': 1, 'num': 0x15},
    'map_colour'               : {'size': 1, 'num': 0x16},
    'introduction_date'        : {'size': 4, 'num': 0x17},
    'requires_railtype_list'   : {'custom_function': lambda x: railtype_list(x, 0x18)},
    'introduces_railtype_list' : {'custom_function': lambda x: railtype_list(x, 0x19)},
    'sort_order'               : {'size': 1, 'num': 0x1A},
    'name'                     : {'size': 2, 'num': 0x1B, 'string': 0xDC},
    'maintenance_cost'         : {'size': 2, 'num': 0x1C},
    'alternative_railtype_list': {'custom_function': lambda x: railtype_list(x, 0x1D)},
}

#
# Feature 0x11 (Airport Tiles)
#

properties[0x11] = {
    'substitute'         : {'size': 1, 'num': 0x08, 'first': None},
    'override'           : {'size': 1, 'num': 0x09},
    # 0A - 0D don't exist (yet?)
    # 0E (callback flags) is not set by user
    'animation_info'     : {'size': 2, 'num': 0x0F, 'value_function': animation_info},
    'animation_speed'    : {'size': 1, 'num': 0x10},
    'animation_triggers' : {'size': 1, 'num': 0x11},
}
