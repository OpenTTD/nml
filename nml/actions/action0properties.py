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

from nml import generic
from nml.expression import ConstantNumeric, ConstantFloat, Array, StringLiteral, Identifier

tilelayout_names = {}

class Action0Property(object):
    """
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
# First a short summary is given, then the recognized characteristics
# are outlined below in more detail.
#
# Summary: If 'string' or 'string_literal' is set, the value should be a
# string or literal string, else the value is a number. 'unit_type' and
# 'unit_conversion' are used to convert user-entered values to nfo values.
# 'custom_function' can be used to create a special mapping of the value to nfo
# properties, else 'num' and 'size' are used to provide a 'normal' action0.
# 'append_function' can be used to append one or more other properties.
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
# the user and the resulting value in nfo. The entered value (possibly converted
# to the appropriate reference unit, see 'unit_type' above) is multiplied by
# this factor and then rounded to an integer to provide the final value.
# This parameter is not required and defaults to 1.
#
# 'custom_function' can be used to bypass the normal way of converting the
# name / value to an Action0Property. This function is called with one argument,
# which is the value of the property. It should return a list of Action0Property.
# To pass extra parameters to the function, a dose of lambda calculus can be used.
# Consult the code for examples.
#
# 'append_function' works similarly to 'custum_function', but instead of
# replacing the normal property generation it merely adds to it. The parameter
# and return value are the same, but now the 'normal' action0 property is
# generated as well.
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

properties = 0x12 * [None]

#
# Some helper functions that are used for multiple features
#

def two_byte_property(value, low_prop, high_prop):
    """
    Decode a two byte value into two action 0 properties.

    @param value: Value to encode.
    @type  value: L{ConstantNumeric}

    @param low_prop: Property number for the low 8 bits of the value.
    @type  low_prop: C{int}

    @param high_prop: Property number for the high 8 bits of the value.
    @type  high_prop: C{int}

    @return: Sequence of two action 0 properties (low part, high part).
    @rtype:  C{list} of L{Action0Property}
    """
    value = value.reduce_constant()
    low_byte = ConstantNumeric(value.value & 0xFF)
    high_byte = ConstantNumeric(value.value >> 8)
    return [Action0Property(low_prop, low_byte, 1), Action0Property(high_prop, high_byte, 1)]

def append_cargo_type(feature):
    propnums = [0x15, 0x10, 0x0C]
    return lambda value: [Action0Property(propnums[feature], ConstantNumeric(0xFF), 1)]

def animation_info(prop_num, value, loop_bit=8, max_frame=253, prop_size=2):
    """
    Convert animation info array of two elements to an animation info property.
    The first is 0/1, and defines whether or not the animation loops. The second is the number of frames, at most 253 frames.

    @param prop_num: Property number.
    @type  prop_num: C{int}

    @param value: Array of animation info.
    @type  value: C{Array}

    @param loop_bit: Bit the loop information is stored.
    @type  loop_bit: C{int}

    @param max_frame: Max frames possible.
    @type  max_frame: C{int}

    @param prop_size: Property size in bytes.
    @type  prop_size: C{int}

    @return: Animation property.
    @rtype:  C{list} of L{Action0Property}
    """
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("animation_info must be an array with exactly 2 constant values", value.pos)
    looping = value.values[0].reduce_constant().value
    frames  = value.values[1].reduce_constant().value
    if looping not in (0, 1):
        raise generic.ScriptError("First field of the animation_info array must be either 0 or 1", value.values[0].pos)
    if frames < 1 or frames > max_frame:
        raise generic.ScriptError("Second field of the animation_info array must be between 1 and " + str(max_frame), value.values[1].pos)

    return [Action0Property(prop_num, ConstantNumeric((looping << loop_bit) + frames - 1), prop_size)]

def cargo_list(value, max_num_cargos, prop_num, prop_size):
    """
    Encode an array of cargo types in a single property. If less than the maximum
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
    cargoes = [val.reduce_constant().value for val in value.values] + [0xFF for _ in range(prop_size)]
    val = 0
    for i in range(prop_size):
        val = val | (cargoes[i] << (i * 8))

    return [Action0Property(prop_num, ConstantNumeric(val), prop_size)]

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

#
# Feature 0x00 (Trains)
#

properties[0x00] = {
    'track_type'                   : {'size': 1, 'num': 0x05},
    'ai_special_flag'              : {'size': 1, 'num': 0x08},
    'speed'                        : {'size': 2, 'num': 0x09, 'unit_type': 'speed', 'unit_conversion': 3.5790976, 'adjust_value': lambda val, unit: ottd_display_speed(val, 1, unit)},
    'power'                        : {'size': 2, 'num': 0x0B, 'unit_type': 'power'},
    'running_cost_factor'          : {'size': 1, 'num': 0x0D},
    'running_cost_base'            : {'size': 4, 'num': 0x0E},
    'sprite_id'                    : {'size': 1, 'num': 0x12},
    'dual_headed'                  : {'size': 1, 'num': 0x13},
    'cargo_capacity'               : {'size': 1, 'num': 0x14},
    'weight'                       : {'custom_function': lambda x: two_byte_property(x, 0x16, 0x24), 'unit_type': 'weight'},
    'cost_factor'                  : {'size': 1, 'num': 0x17},
    'ai_engine_rank'               : {'size': 1, 'num': 0x18},
    'engine_class'                 : {'size': 1, 'num': 0x19},
    'extra_power_per_wagon'        : {'size': 2, 'num': 0x1B, 'unit_type': 'power'},
    'refit_cost'                   : {'size': 1, 'num': 0x1C},
    'refittable_cargo_types'       : {'size': 4, 'num': 0x1D, 'append_function': append_cargo_type(0x00)},
    'callback_flags'               : {'size': 1, 'num': 0x1E},
    'tractive_effort_coefficient'  : {'size': 1, 'num': 0x1F, 'unit_conversion': 255},
    'air_drag_coefficient'         : {'size': 1, 'num': 0x20, 'unit_conversion': 255},
    'shorten_vehicle'              : {'size': 1, 'num': 0x21},
    'visual_effect_and_powered'    : {'size': 1, 'num': 0x22},
    'extra_weight_per_wagon'       : {'size': 1, 'num': 0x23, 'unit_type': 'weight'},
    'bitmask_vehicle_info'         : {'size': 1, 'num': 0x25},
    'retire_early'                 : {'size': 1, 'num': 0x26},
    'misc_flags'                   : {'size': 1, 'num': 0x27},
    'refittable_cargo_classes'     : {'size': 2, 'num': 0x28, 'append_function': append_cargo_type(0x00)},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x29, 'append_function': append_cargo_type(0x00)},
    'introduction_date'            : {'size': 4, 'num': 0x2A},
    'cargo_age_period'             : {'size': 2, 'num': 0x2B},
}
properties[0x00].update(general_veh_props)

#
# Feature 0x01 (Road Vehicles)
#

def roadveh_speed_prop(value):
    value = value.reduce_constant()
    prop08 = ConstantNumeric(min(value.value, 0xFF))
    props = [Action0Property(0x08, prop08, 1)]
    if value.value > 0xFF:
        prop15 = ConstantNumeric((value.value + 3) / 4)
        props.append(Action0Property(0x15, prop15, 1))
    return props

properties[0x01] = {
    'speed'                        : {'custom_function' : roadveh_speed_prop, 'unit_type': 'speed', 'unit_conversion': 7.1581952, 'adjust_value': lambda val, unit: ottd_display_speed(val, 2, unit)},
    'running_cost_factor'          : {'size': 1, 'num': 0x09},
    'running_cost_base'            : {'size': 4, 'num': 0x0A},
    'sprite_id'                    : {'size': 1, 'num': 0x0E},
    'cargo_capacity'               : {'size': 1, 'num': 0x0F},
    'cost_factor'                  : {'size': 1, 'num': 0x11},
    'sound_effect'                 : {'size': 1, 'num': 0x12},
    'power'                        : {'size': 1, 'num': 0x13, 'unit_type': 'power', 'unit_conversion': 0.1},
    'weight'                       : {'size': 1, 'num': 0x14, 'unit_type': 'weight', 'unit_conversion': 4},
    'refittable_cargo_types'       : {'size': 4, 'num': 0x16, 'append_function': append_cargo_type(0x01)},
    'callback_flags'               : {'size': 1, 'num': 0x17},
    'tractive_effort_coefficient'  : {'size': 1, 'num': 0x18, 'unit_conversion': 255},
    'air_drag_coefficient'         : {'size': 1, 'num': 0x19, 'unit_conversion': 255},
    'refit_cost'                   : {'size': 1, 'num': 0x1A},
    'retire_early'                 : {'size': 1, 'num': 0x1B},
    'misc_flags'                   : {'size': 1, 'num': 0x1C},
    'refittable_cargo_classes'     : {'size': 2, 'num': 0x1D, 'append_function': append_cargo_type(0x01)},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x1E, 'append_function': append_cargo_type(0x01)},
    'introduction_date'            : {'size': 4, 'num': 0x1F},
    'visual_effect'                : {'size': 1, 'num': 0x21},
    'cargo_age_period'             : {'size': 2, 'num': 0x22},
}
properties[0x01].update(general_veh_props)

#
# Feature 0x02 (Ships)
#

def speed_fraction_prop(value, propnr):
    # Unit is already converted to 0 .. 255 range when we get here
    value = value.reduce_constant()
    if not (0 <= value.value <= 255):
        # Do not use check_range to provide better error message
        raise generic.ScriptError("speed fraction must be in range 0 .. 1", value.pos)
    value = ConstantNumeric(255 - value.value, value.pos)
    return [Action0Property(propnr, value, 1)]

properties[0x02] = {
    'sprite_id'                    : {'size': 1, 'num': 0x08},
    'is_refittable'                : {'size': 1, 'num': 0x09},
    'cost_factor'                  : {'size': 1, 'num': 0x0A},
    'speed'                        : {'size': 1, 'num': 0x0B, 'unit_type': 'speed', 'unit_conversion': 7.1581952, 'adjust_value': lambda val, unit: ottd_display_speed(val, 2, unit)},
    'cargo_capacity'               : {'size': 2, 'num': 0x0D},
    'running_cost_factor'          : {'size': 1, 'num': 0x0F},
    'sound_effect'                 : {'size': 1, 'num': 0x10},
    'refittable_cargo_types'       : {'size': 4, 'num': 0x11, 'append_function': append_cargo_type(0x02)},
    'callback_flags'               : {'size': 1, 'num': 0x12},
    'refit_cost'                   : {'size': 1, 'num': 0x13},
    'ocean_speed_fraction'         : {'size': 1, 'num': 0x14, 'unit_conversion': 255, 'custom_function': lambda val: speed_fraction_prop(val, 0x14)},
    'canal_speed_fraction'         : {'size': 1, 'num': 0x15, 'unit_conversion': 255, 'custom_function': lambda val: speed_fraction_prop(val, 0x15)},
    'retire_early'                 : {'size': 1, 'num': 0x16},
    'misc_flags'                   : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes'     : {'size': 2, 'num': 0x18, 'append_function': append_cargo_type(0x02)},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19, 'append_function': append_cargo_type(0x02)},
    'introduction_date'            : {'size': 4, 'num': 0x1A},
    'visual_effect'                : {'size': 1, 'num': 0x1C},
    'cargo_age_period'             : {'size': 2, 'num': 0x1D},
}
properties[0x02].update(general_veh_props)

#
# Feature 0x03 (Aircraft)
#

properties[0x03] = {
    'sprite_id'                    : {'size': 1, 'num': 0x08},
    'is_helicopter'                : {'size': 1, 'num': 0x09},
    'is_large'                     : {'size': 1, 'num': 0x0A},
    'cost_factor'                  : {'size': 1, 'num': 0x0B},
    'speed'                        : {'size': 1, 'num': 0x0C, 'unit_type': 'speed', 'unit_conversion': 0.279617, 'adjust_value': lambda val, unit: ottd_display_speed(val, 1, unit)},
    'acceleration'                 : {'size': 1, 'num': 0x0D},
    'running_cost_factor'          : {'size': 1, 'num': 0x0E},
    'passenger_capacity'           : {'size': 2, 'num': 0x0F},
    'mail_capacity'                : {'size': 1, 'num': 0x11},
    'sound_effect'                 : {'size': 1, 'num': 0x12},
    'refittable_cargo_types'       : {'size': 4, 'num': 0x13},
    'callback_flags'               : {'size': 1, 'num': 0x14},
    'refit_cost'                   : {'size': 1, 'num': 0x15},
    'retire_early'                 : {'size': 1, 'num': 0x16},
    'misc_flags'                   : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes'     : {'size': 2, 'num': 0x18},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19},
    'introduction_date'            : {'size': 4, 'num': 0x1A},
    'cargo_age_period'             : {'size': 2, 'num': 0x1C},
}
properties[0x03].update(general_veh_props)

# TODO: Feature 0x04 .. 0x06 (Stations, Canals, Bridges)

properties[0x05] = {
    'callback_flags' : {'size': 1, 'num': 0x08},
    'graphic_flags'  : {'size': 1, 'num': 0x09},
}

#
# Feature 0x07 (Houses)
#

def house_available_years(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Availability years must be an array with exactly two values", value.pos)
    min_year = value.values[0].reduce_constant().value
    max_year = value.values[1].reduce_constant().value
    min_year_safe = min(max(min_year - 1920, 0), 255)
    max_year_safe = min(max(max_year - 1920, 0), 255)
    return [Action0Property(0x0A, ConstantNumeric(max_year_safe << 8 | min_year_safe), 2),
            Action0Property(0x21, ConstantNumeric(min_year), 2),
            Action0Property(0x22, ConstantNumeric(max_year), 2)]

def house_random_colours(value):
    if not isinstance(value, Array) or len(value.values) != 4:
        raise generic.ScriptError("Random colours must be an array with exactly four values", value.pos)
    colours = [val.reduce_constant().value for val in value.values]
    for colour in colours:
        if colour < 0 or colour > 15:
            raise generic.ScriptError("Random house colours must be a value between 0 and 15", value.pos)
    return [Action0Property(0x17, ConstantNumeric(colours[0] << 24 | colours[1] << 16 | colours[2] << 8 | colours[3]), 4)]

def house_available_mask(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("availability_mask must be an array with exactly 2 values", value.pos)
    town_zones = value.values[0].reduce_constant().value
    climates = value.values[1].reduce_constant().value
    return [Action0Property(0x13, ConstantNumeric(town_zones | (climates & 0x800) | ((climates & 0x0F) << 12)), 2)]

properties[0x07] = {
    'substitute'              : {'size': 1, 'num': 0x08},
    'building_flags'          : {'custom_function': lambda x: two_byte_property(x, 0x09, 0x19)},
    'years_available'         : {'custom_function': house_available_years},
    'population'              : {'size': 1, 'num': 0x0B},
    'mail_multiplier'         : {'size': 1, 'num': 0x0C},
    'pax_acceptance'          : {'size': 1, 'num': 0x0D, 'unit_conversion': 8},
    'mail_acceptance'         : {'size': 1, 'num': 0x0E, 'unit_conversion': 8},
    'cargo_acceptance'        : {'size': 1, 'num': 0x0F, 'unit_conversion': 8},
    'local_authority_impact'  : {'size': 2, 'num': 0x10},
    'removal_cost_multiplier' : {'size': 1, 'num': 0x11},
    'name'                    : {'size': 2, 'num': 0x12, 'string': 0xDC},
    'availability_mask'       : {'custom_function': house_available_mask},
    'callback_flags'          : {'custom_function': lambda x: two_byte_property(x, 0x14, 0x1D)},
    'override'                : {'size': 1, 'num': 0x15},
    'refresh_multiplier'      : {'size': 1, 'num': 0x16},
    'random_colours'          : {'custom_function': house_random_colours},
    'probability'             : {'size': 1, 'num': 0x18, 'unit_conversion': 16},
    'animation_info'          : {'custom_function': lambda value: animation_info(0x1A, value, 7, 128, 1)},
    'animation_speed'         : {'size': 1, 'num': 0x1B},
    'building_class'          : {'size': 1, 'num': 0x1C},
    'accepted_cargos'         : {'custom_function': lambda value: cargo_list(value, 3, 0x1E, 4)},
    'minimum_lifetime'        : {'size': 1, 'num': 0x1F},
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
    'substitute'         : {'size': 1, 'num': 0x08},
    'override'           : {'size': 1, 'num': 0x09},
    'accepted_cargos'    : {'custom_function': industrytile_cargos},
    'land_shape_flags'   : {'size': 1, 'num': 0x0D},
    'callback_flags'     : {'size': 1, 'num': 0x0E},
    'animation_info'     : {'custom_function': lambda value: animation_info(0x0F, value)},
    'animation_speed'    : {'size': 1, 'num': 0x10},
    'animation_triggers' : {'size': 1, 'num': 0x11},
    'special_flags'      : {'size': 1, 'num': 0x12},
}

#
# Feature 0x0A (Industries)
#

class IndustryLayoutProp(object):
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

class RandomSoundsProp(object):
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

class ConflictingTypesProp(object):
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
    'substitute'             : {'size': 1, 'num': 0x08},
    'override'               : {'size': 1, 'num': 0x09},
    'layouts'                : {'custom_function': industry_layouts},
    'life_type'              : {'size': 1, 'num': 0x0B},
    'closure_msg'            : {'size': 2, 'num': 0x0C},
    'prod_increase_msg'      : {'size': 2, 'num': 0x0D},
    'prod_decrease_msg'      : {'size': 2, 'num': 0x0E},
    'fund_cost_multiplier'   : {'size': 1, 'num': 0x0F},
    'prod_cargo_types'       : {'custom_function': lambda value: cargo_list(value, 2, 0x10, 2)},
    'accept_cargo_types'     : {'custom_function': lambda value: cargo_list(value, 3, 0x11, 4)},
    'prod_multiplier'        : {'custom_function': industry_prod_multiplier},
    'min_cargo_distr'        : {'size': 1, 'num': 0x14},
    'random_sound_effects'   : {'custom_function': random_sounds},
    'conflicting_ind_types'  : {'custom_function': industry_conflicting_types},
    'prob_random'            : {'size': 1, 'num': 0x17},
    'prob_in_game'           : {'size': 1, 'num': 0x18},
    'map_colour'             : {'size': 1, 'num': 0x19},
    'spec_flags'             : {'size': 4, 'num': 0x1A},
    'new_ind_msg'            : {'size': 2, 'num': 0x1B},
    'input_multiplier_1'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1C)},
    'input_multiplier_2'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1D)},
    'input_multiplier_3'     : {'custom_function': lambda value: industry_input_multiplier(value, 0x1E)},
    'name'                   : {'size': 2, 'num': 0x1F, 'string': 0xDC},
    'prospect_chance'        : {'size': 4, 'num': 0x20, 'unit_conversion': 0xFFFFFFFF},
    'callback_flags'         : {'custom_function': lambda x: two_byte_property(x, 0x21, 0x22)},
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
    'single_unit_text'          : {'num' : 0x0B, 'size' : 2, 'string' : 0xDC},
    'multiple_units_text'       : {'num' : 0x0C, 'size' : 2, 'string' : 0xDC},
    'type_abbreviation'         : {'num' : 0x0D, 'size' : 2, 'string' : 0xDC},
    'sprite'                    : {'num' : 0x0E, 'size' : 2},
    'weight'                    : {'num' : 0x0F, 'size' : 1, 'unit_type' : 'weight', 'unit_conversion' : 16},
    'penalty_lowerbound'        : {'num' : 0x10, 'size' : 1},
    'single_penalty_length'     : {'num' : 0x11, 'size' : 1},
    'price_factor'              : {'num' : 0x12, 'size' : 4, 'unit_conversion' : (1 << 21) / (10.0 * 20 * 255)}, # 10 units of cargo across 20 tiles, with time factor = 255
    'station_list_colour'       : {'num' : 0x13, 'size' : 1},
    'cargo_payment_list_colour' : {'num' : 0x14, 'size' : 1},
    'is_freight'                : {'num' : 0x15, 'size' : 1},
    'cargo_classes'             : {'num' : 0x16, 'size' : 2},
    'cargo_label'               : {'num' : 0x17, 'size' : 4, 'string_literal': 4},
    'town_growth_effect'        : {'num' : 0x18, 'size' : 1},
    'town_growth_multiplier'    : {'num' : 0x19, 'size' : 2, 'unit_conversion' : 0x100},
    'callback_flags'            : {'num' : 0x1A, 'size' : 1},
    'units_of_cargo'            : {'num' : 0x1B, 'size' : 2, 'string' : 0xDC},
    'items_of_cargo'            : {'num' : 0x1C, 'size' : 2, 'string' : 0xDC},
}

# TODO: Feature 0x0C (Sound Effects)

#
# Feature 0x0D (Airports)
#

def airport_years(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Availability years must be an array with exactly two values", value.pos)
    min_year = value.values[0].reduce_constant()
    max_year = value.values[1].reduce_constant()
    return [Action0Property(0x0C, ConstantNumeric(max_year.value << 16 | min_year.value), 4)]

class AirportLayoutProp(object):
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
    'override'         : {'size': 1, 'num': 0x08},
    'layouts'          : {'custom_function': airport_layouts},
    'years_available'  : {'custom_function': airport_years},
    'ttd_airport_type' : {'size': 1, 'num': 0x0D},
    'catchment_area'   : {'size': 1, 'num': 0x0E},
    'noise_level'      : {'size': 1, 'num': 0x0F},
    'name'             : {'size': 2, 'num': 0x10, 'string': 0xDC},
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
    'class'                  : {'size': 4, 'num': 0x08, 'string_literal': 4},
    # strings might be according to specs be either 0xD0 or 0xD4
    'classname'              : {'size': 2, 'num': 0x09, 'string': 0xD0},
    'name'                   : {'size': 2, 'num': 0x0A, 'string': 0xD0},
    'climates_available'     : {'size': 1, 'num': 0x0B},
    'size'                   : {'custom_function': object_size},
    'build_cost_multiplier'  : {'size': 1, 'num': 0x0D},
    'introduction_date'      : {'size': 4, 'num': 0x0E},
    'end_of_life_date'       : {'size': 4, 'num': 0x0F},
    'object_flags'           : {'size': 2, 'num': 0x10},
    'animation_info'         : {'custom_function': lambda value: animation_info(0x11, value)},
    'animation_speed'        : {'size': 1, 'num': 0x12},
    'animation_triggers'     : {'size': 2, 'num': 0x13},
    'remove_cost_multiplier' : {'size': 1, 'num': 0x14},
    'callback_flags'         : {'size': 2, 'num': 0x15},
    'height'                 : {'size': 1, 'num': 0x16},
    'num_views'              : {'size': 1, 'num': 0x17},
}

#
# Feature 0x10 (Rail Types)
#

class RailtypeListProp(object):
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
    'label'                    : {'size': 4, 'num': 0x08, 'string_literal': 4},
    'name'                     : {'size': 2, 'num': 0x09, 'string': 0xDC},
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
    'speed_limit'              : {'size': 2, 'num': 0x14, 'unit_type': 'speed', 'unit_conversion': 3.5790976},
    'acceleration_model'       : {'size': 1, 'num': 0x15},
    'map_colour'               : {'size': 1, 'num': 0x16},
    'introduction_date'        : {'size': 4, 'num': 0x17},
    'requires_railtype_list'   : {'custom_function': lambda x: railtype_list(x, 0x18)},
    'introduces_railtype_list' : {'custom_function': lambda x: railtype_list(x, 0x19)},
    'sort_order'               : {'size': 1, 'num': 0x1A},
}

#
# Feature 0x11 (Airport Tiles)
#

properties[0x11] = {
    'substitute'         : {'size': 1, 'num': 0x08},
    'override'           : {'size': 1, 'num': 0x09},
    'callback_flags'     : {'size': 1, 'num': 0x0E},
    'animation_info'     : {'custom_function': lambda value: animation_info(0x0F, value)},
    'animation_speed'    : {'size': 1, 'num': 0x10},
    'animation_triggers' : {'size': 1, 'num': 0x11},
}
