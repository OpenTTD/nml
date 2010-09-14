from nml import generic
from nml.expression import ConstantNumeric, Array, StringLiteral, Identifier

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

    def write(self, file):
        file.print_bytex(self.num)
        for val in self.values:
            val.write(file, self.size)
        file.newline()

    def get_size(self):
        return self.size * len(self.values) + 1

properties = 0x12 * [None]

def two_byte_property(value, low_prop, high_prop):
    value = value.reduce_constant()
    low_byte = ConstantNumeric(value.value & 0xFF)
    high_byte = ConstantNumeric(value.value >> 8)
    return [Action0Property(low_prop, low_byte, 1), Action0Property(high_prop, high_byte, 1)]

general_veh_props = {
    'reliability_decay' : {'size': 1, 'num': 0x02},
    'vehicle_life' : {'size': 1, 'num': 0x03},
    'model_life' : {'size': 1, 'num': 0x04},
    'climates_available' : {'size': 1, 'num': 0x06},
    'loading_speed' : {'size': 1, 'num': 0x07},
    'name': {'num': -1, 'string': None},
}

properties[0x00] = {
    'track_type' : {'size': 1, 'num': 0x05},
    'ai_special_flag' : {'size': 1, 'num': 0x08},
    'speed' : {'size': 2, 'num': 0x09, 'unit_type': 'speed', 'unit_conversion': 3.5790976},
    'power' : {'size': 2, 'num': 0x0B, 'unit_type': 'power'},
    'running_cost_factor' : {'size': 1, 'num': 0x0D},
    'running_cost_base' : {'size': 4, 'num': 0x0E},
    'sprite_id' : {'size': 1, 'num': 0x12},
    'dual_headed' : {'size': 1, 'num': 0x13},
    'cargo_capacity' : {'size': 1, 'num': 0x14},
    'cargo_type' : {'size': 1, 'num': 0x15},
    'weight' : {'custom_function': lambda x: two_byte_property(x, 0x16, 0x24), 'unit_type': 'weight'},
    'cost_factor' : {'size': 1, 'num': 0x17},
    'ai_engine_rank' : {'size': 1, 'num': 0x18},
    'engine_class' : {'size': 1, 'num': 0x19},
    'extra_power_per_wagon' : {'size': 2, 'num': 0x1B, 'unit_type': 'power'},
    'refit_cost' : {'size': 1, 'num': 0x1C},
    'refittable_cargo_types' : {'size': 4, 'num': 0x1D},
    'callback_flags' : {'size': 1, 'num': 0x1E},
    'tractive_effort_coefficient' : {'size': 1, 'num': 0x1F, 'unit_conversion': 255},
    'air_drag_coefficient' : {'size': 1, 'num': 0x20, 'unit_conversion': 255},
    'shorten_vehicle' : {'size': 1, 'num': 0x21},
    'visual_effect' : {'size': 1, 'num': 0x22},
    'extra_weight_per_wagon' : {'size': 1, 'num': 0x23, 'unit_type': 'weight'},
    'bitmask_vehicle_info' : {'size': 1, 'num': 0x25},
    'retire_early' : {'size': 1, 'num': 0x26},
    'misc_flags' : {'size': 1, 'num': 0x27},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x28},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x29},
    'introduction_date' : {'size': 4, 'num': 0x2A},
}
properties[0x00].update(general_veh_props)


def roadveh_speed_prop(value):
    value = value.reduce_constant()
    prop08 = ConstantNumeric(min(value.value, 0xFF))
    prop15 = ConstantNumeric(value.value / 4)
    return [Action0Property(0x08, prop08, 1), Action0Property(0x15, prop15, 1)]

properties[0x01] = {
    'speed': {'custom_function': roadveh_speed_prop, 'unit_type': 'speed', 'unit_conversion': 7.1581952},
    'running_cost_factor' : {'size': 1, 'num': 0x09},
    'running_cost_base' : {'size': 4, 'num': 0x0A},
    'sprite_id' : {'size': 1, 'num': 0x0E},
    'cargo_capacity' : {'size': 1, 'num': 0x0F},
    'cargo_type' : {'size': 1, 'num': 0x10},
    'cost_factor' : {'size': 1, 'num': 0x11},
    'sound_effect' : {'size': 1, 'num': 0x12},
    'power' : {'size': 1, 'num': 0x13, 'unit_type': 'power', 'unit_conversion': 0.1},
    'weight' : {'size': 1, 'num': 0x14, 'unit_type': 'weight'},
    'refittable_cargo_types' : {'size': 4, 'num': 0x16},
    'callback_flags' : {'size': 1, 'num': 0x17},
    'tractive_effort_coefficient' : {'size': 1, 'num': 0x18, 'unit_conversion': 255},
    'air_drag_coefficient' : {'size': 1, 'num': 0x19, 'unit_conversion': 255},
    'refit_cost' : {'size': 1, 'num': 0x1A},
    'retire_early' : {'size': 1, 'num': 0x1B},
    'misc_flags' : {'size': 1, 'num': 0x1C},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x1D},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x1E},
    'introduction_date' : {'size': 4, 'num': 0x1F},
}
properties[0x01].update(general_veh_props)

properties[0x02] = {
    'sprite_id' : {'size': 1, 'num': 0x08},
    'is_refittable' : {'size': 1, 'num': 0x09},
    'cost_factor' : {'size': 1, 'num': 0x0A},
    'speed' : {'size': 1, 'num': 0x0B, 'unit_type': 'speed', 'unit_conversion': 7.1581952},
    'cargo_type' : {'size': 1, 'num': 0x0C},
    'cargo_capacity' : {'size': 2, 'num': 0x0D},
    'running_cost_factor' : {'size': 1, 'num': 0x0F},
    'sound_effect' : {'size': 1, 'num': 0x10},
    'refittable_cargo_types' : {'size': 4, 'num': 0x11},
    'callback_flags' : {'size': 1, 'num': 0x12},
    'refit_cost' : {'size': 1, 'num': 0x15},
    'ocean_speed_fraction' : {'size': 1, 'num': 0x14},
    'canal_speed_fraction' : {'size': 1, 'num': 0x15},
    'retire_early' : {'size': 1, 'num': 0x16},
    'misc_flags' : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x18},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19},
    'introduction_date' : {'size': 4, 'num': 0x1A},
}
properties[0x02].update(general_veh_props)

properties[0x03] = {
    'sprite_id' : {'size': 1, 'num': 0x08},
    'is_helicopter' : {'size': 1, 'num': 0x09},
    'is_large' : {'size': 1, 'num': 0x0A},
    'cost_factor' : {'size': 1, 'num': 0x0B},
    'speed' : {'size': 1, 'num': 0x0C, 'unit_type': 'speed', 'unit_conversion': 0.279617},
    'acceleration' : {'size': 1, 'num': 0x0D},
    'running_cost_factor' : {'size': 1, 'num': 0x0D},
    'passenger_capacity' : {'size': 2, 'num': 0x0F},
    'mail_capacity' : {'size': 1, 'num': 0x11},
    'sound_effect' : {'size': 1, 'num': 0x12},
    'refittable_cargo_types' : {'size': 4, 'num': 0x13},
    'callback_flags' : {'size': 1, 'num': 0x14},
    'refit_cost' : {'size': 1, 'num': 0x15},
    'retire_early' : {'size': 1, 'num': 0x16},
    'misc_flags' : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x18},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19},
    'introduction_date' : {'size': 4, 'num': 0x1A},
}
properties[0x03].update(general_veh_props)

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

def house_random_colors(value):
    if not isinstance(value, Array) or len(value.values) != 4:
        raise generic.ScriptError("Random colors must be an array with exactly four values", value.pos)
    colors = [val.reduce_constant().value for val in value.values]
    for color in colors:
        if color < 0 or color > 15:
            raise generic.ScriptError("Random house colors must be a value between 0 and 15", value.pos)
    return [Action0Property(0x17, ConstantNumeric(colors[0] << 24 | colors[1] << 16 | colors[2] << 8 | colors[3]), 4)]

def house_accepted_cargos(value):
    if not isinstance(value, Array) or len(value.values) > 3:
        raise generic.ScriptError("Accepted cargos must be an array with no more than 3 values", value.pos)
    cargoes = [val.reduce_constant().value for val in value.values]
    val = 0
    for i in range(4):
        if i < len(cargoes):
            val = val | (cargoes[i] << (i * 8))
        else:
            val = val | (0xFF << (i * 8))
    return [Action0Property(0x1E, ConstantNumeric(val), 4)]

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
    'availability_mask'       : {'size': 2, 'num': 0x13},
    'callback_flags'          : {'custom_function': lambda x: two_byte_property(x, 0x14, 0x1D)},
    'override'                : {'size': 1, 'num': 0x15},
    'refresh_multiplier'      : {'size': 1, 'num': 0x16},
    'random_colours'          : {'custom_function': house_random_colors},
    'probability'             : {'size': 1, 'num': 0x18},
    'animation_frames'        : {'size': 1, 'num': 0x1A},
    'animation_speed'         : {'size': 1, 'num': 0x1B},
    'building_class'          : {'size': 1, 'num': 0x1C},
    'accepted_cargos'         : {'custom_function': house_accepted_cargos},
    'minimum_lifetime'        : {'size': 1, 'num': 0x1F},
}

properties[0x09] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'cargo_1': {'size': 2, 'num': 0x0A},
    'cargo_2': {'size': 2, 'num': 0x0B},
    'cargo_3': {'size': 2, 'num': 0x0C},
    'land_shape_flags': {'size': 1, 'num': 0x0D},
    'callback_flags': {'size': 1, 'num': 0x0E},
    'animation_info': {'size': 2, 'num': 0x0F},
    'animation_speed': {'size': 1, 'num': 0x10},
    'triggers_cb25': {'size': 1, 'num': 0x11},
    'special_flags': {'size': 1, 'num': 0x12},
}

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

properties[0x0A] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'layouts': {'custom_function': industry_layouts},
    'prod_flags': {'size': 1, 'num': 0x0B},
    'closure_msg': {'size': 2, 'num': 0x0C},
    'prod_increase_msg': {'size': 2, 'num': 0x0D},
    'prod_decrease_msg': {'size': 2, 'num': 0x0E},
    'fund_cost_multiplier': {'size': 1, 'num': 0x0F},
    'prod_cargo_types': {'size': 2, 'num': 0x10},
    'accept_cargo_types': {'size': 4, 'num': 0x11},
    'prod_multiplier_1': {'size': 1, 'num': 0x12},
    'prod_multiplier_2': {'size': 1, 'num': 0x13},
    'min_cargo_distr': {'size': 1, 'num': 0x14},
    'random_sound_effects': {'size': 0, 'num': 0x15},
    'conflicting_ind_types': {'size': 0, 'num': 0x16},
    'prob_random': {'size': 1, 'num': 0x17},
    'prob_in_game': {'size': 1, 'num': 0x18},
    'map_color': {'size': 1, 'num': 0x19},
    'spec_flags': {'size': 4, 'num': 0x1A},
    'new_ind_text': {'size': 2, 'num': 0x1B},
    'input_multiplier_1': {'size': 4, 'num': 0x1C},
    'input_multiplier_2': {'size': 4, 'num': 0x1D},
    'input_multiplier_3': {'size': 4, 'num': 0x1E},
    'name': {'size': 2, 'num': 0x1F, 'string': 0xDC},
    'prospect_chance': {'size': 4, 'num': 0x20, 'unit_conversion': 0xFFFFFFFF},
    'callback_flags': {'custom_function': lambda x: two_byte_property(x, 0x21, 0x22)},
    'remove_cost_multiplier': {'size': 4, 'num': 0x23},
    'nearby_station_name': {'size': 2, 'num': 0x24, 'string': 0xDC},
}

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
        layouts.append(layout)
    return [AirportLayoutProp(layouts)]

properties[0x0D] = {
    'override': {'size': 1, 'num': 0x08},
    'layouts': {'custom_function': airport_layouts},
    'years_available': {'custom_function': airport_years},
    'ttd_airport_type': {'size': 1, 'num': 0x0D},
    'catchment_area': {'size': 1, 'num': 0x0E},
    'noise_level': {'size': 1, 'num': 0x0F},
    'name': {'size': 2, 'num': 0x10, 'string': 0xDC},
}

def object_size(value):
    if not isinstance(value, Array) or len(value.values) != 2:
        raise generic.ScriptError("Object size must be an array with exactly two values", value.pos)
    sizex = value.values[0].reduce_constant()
    sizey = value.values[1].reduce_constant()
    if sizex.value < 1 or sizex.value > 15 or sizey.value < 1 or sizey.value > 15:
        raise generic.ScriptError("The size of an object must be at least 1x1 and at most 15x15 tiles", value.pos)
    return [Action0Property(0x0C, ConstantNumeric(sizey.value << 8 | sizex.value), 1)]

properties[0x0F] = {
    'class': {'size': 4, 'num': 0x08, 'string_literal': 4},
    # strings might be according to specs be either 0xD0 or 0xD4
    'classname': {'size': 2, 'num': 0x09, 'string': 0xD0},
    'build_window_caption': {'size': 2, 'num': 0x0A, 'string': 0xD0},
    'climates_available' : {'size': 1, 'num': 0x0B},
    'size': {'custom_function': object_size},
    'build_cost_multiplier': {'size': 1, 'num': 0x0D},
    'introduction_date': {'size': 4, 'num': 0x0E},
    'end_of_life_date': {'size': 4, 'num': 0x0F},
    'object_flags': {'size': 2, 'num': 0x10},
    'animation_info': {'size': 2, 'num': 0x11},
    'animation_speed': {'size': 1, 'num': 0x12},
    'animation_triggers': {'size': 1, 'num': 0x13},
    'remove_cost_multiplier': {'size': 1, 'num': 0x14},
    'callback_flags': {'size': 2, 'num': 0x15},
    'height': {'size': 1, 'num': 0x16},
}

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
    'label': {'size': 4, 'num': 0x08, 'string_literal': 4},
    'name': {'size': 2, 'num': 0x09, 'string': 0xDC},
    'menu_text': {'size': 2, 'num': 0x0A, 'string': 0xDC},
    'build_window_caption': {'size': 2, 'num': 0x0B, 'string': 0xDC},
    'autoreplace_text': {'size': 2, 'num': 0x0C, 'string': 0xDC},
    'new_engine_text': {'size': 2, 'num': 0x0D, 'string': 0xDC},
    'compatible_railtype_list': {'custom_function': lambda x: railtype_list(x, 0x0E)},
    'powered_railtype_list': {'custom_function': lambda x: railtype_list(x, 0x0F)},
    'railtype_flags': {'size': 1, 'num': 0x10},
    'curve_speed_multiplier': {'size': 1, 'num': 0x11},
    'station_graphics': {'size': 1, 'num': 0x12},
    'construction_cost': {'size': 2, 'num': 0x13},
    'speed_limit': {'size': 2, 'num': 0x14, 'unit_type': 'speed', 'unit_conversion': 3.5790976},
    'acceleration_model': {'size': 1, 'num': 0x15},
    'map_color': {'size': 1, 'num': 0x16},
}

properties[0x11] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'callback_flags': {'size': 1, 'num': 0x0E},
    'animation_info': {'size': 2, 'num': 0x0F},
    'animation_speed': {'size': 1, 'num': 0x10},
    'animation_triggers': {'size': 1, 'num': 0x11},
}
