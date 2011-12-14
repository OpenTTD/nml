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

from nml import expression, nmlop, generic

# Use feature 0x12 for towns (accessible via station/house/industry parent scope)
varact2vars = 0x13 * [{}]
varact2vars60x = 0x13 * [{}]
# feature number:      0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x12, None, 0x12, 0x12, None, 0x0A, 0x12, None, None, None, None, 0x12, None, None, None]

def default_60xvar(name, args, pos, info):
    """
    Function to convert arguments into a variable parameter.
    This function handles the default case of one argument.

    @param name: Name of the variable
    @type name: C{str}

    @param args: List of passed arguments
    @type args: C{list} of L{Expression}

    @param pos: Position information
    @type pos: L{Position}

    @param info: Information of the variable, as found in the dictionary
    @type info: C{dict}

    @return: A tuple of two values:
                - Parameter to use for the 60+x variable
                - List of possible extra parameters that need to be passed via registers
    @rtype: C{tuple} of (L{Expression}, C{list} C{tuple} of (C{int}, L{Expression}))
    """
    if len(args) != 1:
        raise generic.ScriptError("'%s'() requires one argument, encountered %d" % (name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):
        generic.check_range(args[0].value, 0, 255, "Argument of '%s'" % name, args[0].pos)
    return (args[0], [])

def signextend(var, info):
    #r = (x ^ m) - m; with m being (1 << (num_bits -1))
    m = expression.ConstantNumeric(1 << (info['size'] - 1))
    return expression.BinOp(nmlop.SUB, expression.BinOp(nmlop.XOR, var, m, var.pos), m, var.pos)

def muldiv(var, mul, div):
    var = expression.BinOp(nmlop.MUL, var, expression.ConstantNumeric(mul, var.pos), var.pos)
    return expression.BinOp(nmlop.DIV, var, expression.ConstantNumeric(div, var.pos), var.pos)

varact2_globalvars = {
    'current_month' : {'var': 0x02, 'start': 0, 'size': 8},
    'current_day_of_month' : {'var': 0x02, 'start': 8, 'size': 5},
    'is_leapyear' : {'var': 0x02, 'start': 15, 'size': 1},
    'current_day_of_year' : {'var': 0x02, 'start': 16, 'size': 9},
    'climate' : {'var': 0x03, 'start': 0, 'size': 2},
    'traffic_side' : {'var': 0x06, 'start': 0, 'size': 8},
    'animation_counter' : {'var': 0x0A, 'start': 0, 'size': 16},
    'current_callback' : {'var': 0x0C, 'start': 0, 'size': 16},
    'extra_callback_info1' : {'var': 0x10, 'start': 0, 'size': 32},
    'game_mode' : {'var': 0x12, 'start': 0, 'size': 8},
    'extra_callback_info2' : {'var': 0x18, 'start': 0, 'size': 32},
    'display_options' : {'var': 0x1B, 'start': 0, 'size': 6},
    'last_computed_result' : {'var': 0x1C, 'start': 0, 'size': 32},
    'snowline_height' : {'var': 0x20, 'start': 0, 'size': 8},
    'difficulty_level' : {'var': 0x22, 'start': 0, 'size': 8},
    'current_date' : {'var': 0x23, 'start': 0, 'size': 32},
    'current_year' : {'var': 0x24, 'start': 0, 'size': 32},
}

def func_add_constant(const):
    return lambda var, info: expression.BinOp(nmlop.ADD, var, expression.ConstantNumeric(const), var.pos)

varact2vars_vehicles = {
    'position_in_consist' : {'var': 0x40, 'start': 0, 'size': 8},
    'position_in_consist_from_end' : {'var': 0x40, 'start': 8, 'size': 8},
    'num_vehs_in_consist' : {'var': 0x40, 'start': 16, 'size': 8, 'function': func_add_constant(1)},
    'position_in_vehid_chain' : {'var': 0x41, 'start': 0, 'size': 8},
    'position_in_vehid_chain_from_end' : {'var': 0x41, 'start': 8, 'size': 8},
    'num_vehs_in_vehid_chain' : {'var': 0x41, 'start': 16, 'size': 8, 'function': func_add_constant(1)},
    'cargo_classes_in_consist' : {'var': 0x42, 'start': 0, 'size': 8},
    'most_common_refit' : {'var': 0x42, 'start': 16, 'size': 8},
    'bitmask_consist_info' : {'var': 0x42, 'start': 24, 'size': 8},
    'company_num' : {'var': 0x43, 'start': 0, 'size': 8},
    'company_type' : {'var': 0x43, 'start': 16, 'size': 2},
    'company_colour1' : {'var': 0x43, 'start': 24, 'size': 4},
    'company_colour2' : {'var': 0x43, 'start': 28, 'size': 4},
    'aircraft_height' : {'var': 0x44, 'start': 8, 'size': 8},
    'airport_type' : {'var': 0x44, 'start': 0, 'size': 8},
    'curv_info_prev_cur' : {'var': 0x45, 'start': 0, 'size': 4, 'function': signextend},
    'curv_info_cur_next' : {'var': 0x45, 'start': 8, 'size': 4, 'function': signextend},
    'curv_info_prev_next' : {'var': 0x45, 'start': 16, 'size': 4, 'function': signextend},
    'curv_info' : {'var': 0x45, 'start': 0, 'size': 12, 'function': lambda var, info: expression.BinOp(nmlop.AND, var, expression.ConstantNumeric(0x0F0F, var.pos), var.pos).reduce()},
    'motion_counter' : {'var': 0x46, 'start': 8, 'size': 4},
    'cargo_type_in_veh' : {'var': 0x47, 'start': 0, 'size': 8},
    'cargo_unit_weight' : {'var': 0x47, 'start': 8, 'size': 8},
    'cargo_classes' : {'var': 0x47, 'start': 16, 'size': 16},
    'vehicle_is_available' : {'var': 0x48, 'start': 0, 'size': 1},
    'vehicle_is_testing' : {'var': 0x48, 'start': 1, 'size': 1},
    'vehicle_is_offered' : {'var': 0x48, 'start': 2, 'size': 1},
    'build_year' : {'var': 0x49, 'start': 0, 'size': 32},
    'direction' : {'var': 0x9F, 'start': 0, 'size': 8},
    'cargo_capacity' : {'var': 0xBA, 'start': 0, 'size': 16},
    'cargo_count' : {'var': 0xBC, 'start': 0, 'size': 16},
    'vehicle_type_id' : {'var': 0xC6, 'start': 0, 'size': 16},
    'cargo_subtype' : {'var': 0xF2, 'start': 0, 'size': 8},
    'vehicle_is_powered' : {'var': 0xFE, 'start': 5, 'size': 1},
    'vehicle_is_not_powered' : {'var': 0xFE, 'start': 6, 'size': 1},
    'vehicle_is_potentially_powered': {'var': 0x4A, 'start': 8, 'size': 1},
    'vehicle_is_reversed' : {'var': 0xFE, 'start': 8, 'size': 1},
    'built_during_preview' : {'var': 0xFE, 'start': 10, 'size': 1},
    'current_railtype' : {'var': 0x4A, 'start': 0, 'size': 8},
    'waiting_triggers' : {'var': 0x5F, 'start': 0, 'size': 8},
    'random_bits' : {'var': 0x5F, 'start': 8, 'size': 8},
    'grfid' : {'var': 0x25, 'start': 0, 'size': 32},
    'vehicle_is_hidden' : {'var': 0xB2, 'start': 0, 'size': 1},
    'vehicle_is_stopped' : {'var': 0xB2, 'start': 1, 'size': 1},
    'vehicle_is_crashed' : {'var': 0xB2, 'start': 7, 'size': 1},
    'vehicle_is_broken' : {'var': 0xCB, 'start': 0, 'size': 8, 'function': lambda var, info: expression.BinOp(nmlop.CMP_EQ, var, expression.ConstantNumeric(1, var.pos), var.pos)},
    'date_of_last_service' : {'var': 0x4B, 'start': 0, 'size': 32},
    'breakdowns_since_last_service' : {'var': 0xCA, 'start': 0, 'size': 8},
    'reliability' : {'var': 0xCE, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 101, 0x10000)},
    'age_in_days' : {'var': 0xC0, 'start': 0, 'size': 16},
    'max_age_in_days' : {'var': 0xC2, 'start': 0, 'size': 16},
}
varact2vars_trains = {
    #0x4786 / 0x10000 is an approximation of 3.5790976, the conversion factor
    #for train speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x4786, 0x10000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x4786, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 7, 'size': 1}
}
varact2vars_trains.update(varact2vars_vehicles)

varact2vars_roadvehs = {
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for road vehicle speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 0, 'size': 8, 'function': lambda var, info: expression.BinOp(nmlop.CMP_EQ, var, expression.ConstantNumeric(0xFE, var.pos))},
}
varact2vars_roadvehs.update(varact2vars_vehicles)

varact2vars_ships = {
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for ship speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 7, 'size': 1}
}
varact2vars_ships.update(varact2vars_vehicles)

varact2vars_aircraft = {
    #0x3939 / 0x1000 is an approximation of 0.279617, the conversion factor
    #for aircraft speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x3939, 0x1000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x3939, 0x1000)},
    #No such thing as identical to vehicle_is_in_depot exists for aircraft
}
varact2vars_aircraft.update(varact2vars_vehicles)

varact2vars60x_vehicles = {
    'count_veh_id': {'var': 0x60, 'start': 0, 'size': 8},
}

varact2vars_canals = {
    'tile_height'  : {'var': 0x80, 'start': 0, 'size': 8, 'function': lambda var, info: muldiv(var, 8, 1)},
    'terrain_type' : {'var': 0x81, 'start': 0, 'size': 8},
    'random_bits'  : {'var': 0x83, 'start': 0, 'size': 8},
}


varact2vars_industrytiles = {
    'construction_state' : {'var': 0x40, 'start': 0, 'size': 2},
    'terrain_type' : {'var': 0x41, 'start': 0, 'size': 8},
    'town_zone': {'var': 0x42, 'start': 0, 'size': 3},
    'relative_x': {'var': 0x43, 'start': 0, 'size': 8},
    'relative_y': {'var': 0x43, 'start': 8, 'size': 8},
    'relative_pos': {'var': 0x43, 'start': 0, 'size': 16},
    'animation_frame': {'var': 0x44, 'start': 0, 'size': 8},
    'random_bits' : {'var': 0x5F, 'start': 8, 'size': 8},
}

def tile_offset(name, args, pos, info, min, max):
    if len(args) != 2:
        raise generic.ScriptError("'%s'() requires 2 arguments, encountered %d" % (name, len(args)), pos)
    for arg in args:
        if isinstance(arg, expression.ConstantNumeric):
            generic.check_range(arg.value, min, max, "Argument of '%s'" % name, arg.pos)

    x = expression.BinOp(nmlop.AND, args[0], expression.ConstantNumeric(0xF), args[0].pos)
    y = expression.BinOp(nmlop.AND, args[1], expression.ConstantNumeric(0xF), args[1].pos)
    # Shift y left by four
    y = expression.BinOp(nmlop.SHIFT_LEFT, y, expression.ConstantNumeric(4), y.pos)
    param = expression.BinOp(nmlop.ADD, x, y, x.pos)
    #Make sure to reduce the result
    return ( param.reduce(), [] )

def signed_tile_offset(name, args, pos, info):
    return tile_offset(name, args, pos, info, -8, 7)

def unsigned_tile_offset(name, args, pos, info):
    return tile_offset(name, args, pos, info, 0, 15)

varact2vars60x_industrytiles = {
    'nearby_tile_slope'            : {'var': 0x60, 'start':  0, 'size':  5, 'function': signed_tile_offset},
    'nearby_tile_is_same_industry' : {'var': 0x60, 'start':  8, 'size':  1, 'function': signed_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x60, 'start':  9, 'size':  1, 'function': signed_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x60, 'start': 10, 'size':  3, 'function': signed_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x60, 'start': 13, 'size':  2, 'function': signed_tile_offset},
    'nearby_tile_height'           : {'var': 0x60, 'start': 16, 'size':  8, 'function': signed_tile_offset},
    'nearby_tile_class'            : {'var': 0x60, 'start': 24, 'size':  4, 'function': signed_tile_offset},
    'nearby_tile_animation_frame'  : {'var': 0x61, 'start':  0, 'size':  8, 'function': signed_tile_offset},
    'nearby_tile_industrytile_id'  : {'var': 0x62, 'start':  0, 'size': 16, 'function': signed_tile_offset},
}

varact2vars_industries = {
    'waiting_cargo_1' : {'var': 0x40, 'start': 0, 'size': 16},
    'waiting_cargo_2' : {'var': 0x41, 'start': 0, 'size': 16},
    'waiting_cargo_3' : {'var': 0x42, 'start': 0, 'size': 16},
    'water_distance' : {'var': 0x43, 'start': 0, 'size': 32},
    'layout_num' : {'var': 0x44, 'start': 0, 'size': 8},
    # bits 0 .. 16 are either useless or already covered by var A7
    'founder_type' : {'var': 0x45, 'start': 16, 'size': 2},
    'founder_colour1' : {'var': 0x45, 'start': 24, 'size': 4},
    'founder_colour2' : {'var': 0x45, 'start': 28, 'size': 4},
    'build_date' : {'var': 0x46, 'start': 0, 'size': 32},
    'random_bits' : {'var': 0x5F, 'start': 8, 'size': 16},
    'produced_cargo_waiting_1' : {'var': 0x8A, 'start': 0, 'size': 16},
    'produced_cargo_waiting_2' : {'var': 0x8C, 'start': 0, 'size': 16},
    'production_level' : {'var': 0x93, 'start': 0, 'size': 8},
    'produced_this_month_1' : {'var': 0x94, 'start': 0, 'size': 16},
    'produced_this_month_2' : {'var': 0x96, 'start': 0, 'size': 16},
    'transported_this_month_1' : {'var': 0x98, 'start': 0, 'size': 16},
    'transported_this_month_2' : {'var': 0x9A, 'start': 0, 'size': 16},
    'transported_last_month_pct_1' : {'var': 0x9C, 'start': 0, 'size': 8, 'function': lambda var, info: muldiv(var, 101, 256)},
    'transported_last_month_pct_2' : {'var': 0x9D, 'start': 0, 'size': 8, 'function': lambda var, info: muldiv(var, 101, 256)},
    'produced_last_month_1' : {'var': 0x9E, 'start': 0, 'size': 16},
    'produced_last_month_2' : {'var': 0xA0, 'start': 0, 'size': 16},
    'transported_last_month_1' : {'var': 0xA2, 'start': 0, 'size': 16},
    'transported_last_month_2' : {'var': 0xA4, 'start': 0, 'size': 16},
    'founder' : {'var': 0xA7, 'start': 0, 'size': 8},
    'colour' : {'var': 0xA8, 'start': 0, 'size': 8},
    'counter' : {'var': 0xAA, 'start': 0, 'size': 16},
    'build_type' : {'var': 0xB3, 'start': 0, 'size': 2},
    'last_accept_date' : {'var': 0xB4, 'start':0, 'size': 16, 'function': func_add_constant(701265)}
}

def industry_count(name, args, pos, info):
    if len(args) < 1 or len(args) > 2:
        raise generic.ScriptError("'%s'() requires between 1 and 2 argument(s), encountered %d" % (name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):
        generic.check_range(args[0].value, 0, 255, "First argument of '%s'" % name, args[0].pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 1 else args[1]
    extra_params = [(0x100, grfid)]

    return (args[0], extra_params)


def industry_layout_count(name, args, pos, info):
    if len(args) < 2 or len(args) > 3:
        raise generic.ScriptError("'%s'() requires between 2 and 3 argument(s), encountered %d" % (name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):
        generic.check_range(args[0].value, 0, 255, "First argument of '%s'" % name, args[0].pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 2 else args[2]

    extra_params = []
    extra_params.append( (0x100, grfid) )
    extra_params.append( (0x101, expression.BinOp(nmlop.AND, args[1], expression.ConstantNumeric(0xFF)).reduce()) )
    return (args[0], extra_params)

def industry_town_count(name, args, pos, info):
    if len(args) < 1 or len(args) > 2:
        raise generic.ScriptError("'%s'() requires between 1 and 2 argument(s), encountered %d" % (name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):
        generic.check_range(args[0].value, 0, 255, "First argument of '%s'" % name, args[0].pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 1 else args[1]

    extra_params = []
    extra_params.append( (0x100, grfid) )
    extra_params.append( (0x101, expression.ConstantNumeric(0x0100).reduce()) )
    return (args[0], extra_params)

varact2vars60x_industries = {
    'nearby_tile_industry_tile_id' : { 'var': 0x60, 'start':  0, 'size': 16, 'function': unsigned_tile_offset },
    'nearby_tile_random_bits'      : { 'var': 0x61, 'start':  0, 'size':  8, 'function': unsigned_tile_offset },
    'nearby_tile_slope'            : { 'var': 0x62, 'start':  0, 'size':  5, 'function': unsigned_tile_offset },
    'nearby_tile_is_water'         : { 'var': 0x62, 'start':  9, 'size':  1, 'function': unsigned_tile_offset },
    'nearby_tile_terrain_type'     : { 'var': 0x62, 'start': 10, 'size':  3, 'function': unsigned_tile_offset },
    'nearby_tile_water_class'      : { 'var': 0x62, 'start': 13, 'size':  2, 'function': unsigned_tile_offset },
    'nearby_tile_height'           : { 'var': 0x62, 'start': 16, 'size':  8, 'function': unsigned_tile_offset },
    'nearby_tile_class'            : { 'var': 0x62, 'start': 24, 'size':  4, 'function': unsigned_tile_offset },
    'nearby_tile_animation_frame'  : { 'var': 0x63, 'start':  0, 'size':  8, 'function': unsigned_tile_offset },
    'town_manhattan_dist'          : { 'var': 0x65, 'start':  0, 'size': 16, 'function': signed_tile_offset },
    'town_zone'                    : { 'var': 0x65, 'start': 16, 'size':  8, 'function': signed_tile_offset },
    'town_euclidean_dist'          : { 'var': 0x66, 'start':  0, 'size': 32, 'function': signed_tile_offset },
    'industry_count'               : { 'var': 0x67, 'start': 16, 'size':  8, 'function': industry_count },
    'industry_distance'            : { 'var': 0x67, 'start':  0, 'size': 16, 'function': industry_count },
    'industry_layout_count'        : { 'var': 0x68, 'start': 16, 'size':  8, 'function': industry_layout_count },
    'industry_layout_distance'     : { 'var': 0x68, 'start':  0, 'size': 16, 'function': industry_layout_count },
    'industry_town_count'          : { 'var': 0x68, 'start': 16, 'size':  8, 'function': industry_town_count },
}

varact2vars_airports = {
    'layout' : {'var': 0x40, 'start': 0, 'size': 32},
}

varact2vars_objects = {
    'relative_x'             : {'var': 0x40, 'start': 0, 'size': 8},
    'relative_y'             : {'var': 0x40, 'start': 8, 'size': 8},
    'relative_pos'           : {'var': 0x40, 'start': 0, 'size': 16},

    'terrain_type'           : { 'var' : 0x41, 'start':  0, 'size':  3 },
    'tile_slope'             : { 'var' : 0x41, 'start':  8, 'size':  5 },

    'build_date'             : { 'var' : 0x42, 'start':  0, 'size': 32 },

    'animation_frame'        : { 'var' : 0x43, 'start':  0, 'size':  8 },
    'company_colour'         : { 'var' : 0x43, 'start':  8, 'size':  8 },

    'owner'                  : { 'var' : 0x44, 'start':  0, 'size':  8 },

    'town_manhattan_dist'    : { 'var' : 0x45, 'start':  0, 'size': 16 },
    'town_zone'              : { 'var' : 0x45, 'start': 16, 'size':  8 },

    'town_euclidean_dist'    : { 'var' : 0x46, 'start':  0, 'size': 32 },
    'view'                   : { 'var' : 0x48, 'start':  0, 'size':  8 },
    'random_bits'            : { 'var' : 0x5F, 'start':  8, 'size':  8 },
}

varact2vars60x_objects = {
    'nearby_tile_object_type'      : { 'var' : 0x60, 'start':  0, 'size': 16, 'function': signed_tile_offset },

    'nearby_tile_random_bits'      : { 'var' : 0x61, 'start':  0, 'size':  8, 'function': signed_tile_offset },

    'nearby_tile_slope'            : { 'var' : 0x62, 'start':  0, 'size':  5, 'function': signed_tile_offset },
    'nearby_tile_is_same_object'   : { 'var' : 0x62, 'start':  8, 'size':  1, 'function': signed_tile_offset },
    'nearby_tile_is_water'         : { 'var' : 0x62, 'start':  9, 'size':  1, 'function': signed_tile_offset },
    'nearby_tile_terrain_type'     : { 'var' : 0x62, 'start': 10, 'size':  3, 'function': signed_tile_offset },
    'nearby_tile_water_class'      : { 'var' : 0x62, 'start': 13, 'size':  2, 'function': signed_tile_offset },
    'nearby_tile_height'           : { 'var' : 0x62, 'start': 16, 'size':  8, 'function': signed_tile_offset },
    'nearby_tile_class'            : { 'var' : 0x62, 'start': 24, 'size':  4, 'function': signed_tile_offset },

    'nearby_tile_animation_frame'  : { 'var' : 0x63, 'start':  0, 'size':  8, 'function': signed_tile_offset },

    'object_count'                 : { 'var' : 0x64, 'start': 16, 'size':  8, 'function': industry_count },
    'object_distance'              : { 'var' : 0x64, 'start':  0, 'size': 16, 'function': industry_count },
}

varact2vars_railtype = {
    'terrain_type' : {'var': 0x40, 'start': 0, 'size': 8},
    'enhanced_tunnels': {'var': 0x41, 'start': 0, 'size': 8},
    'level_crossing_status': {'var': 0x42, 'start': 0, 'size': 8},
    'build_date': {'var': 0x43, 'start': 0, 'size': 32},
    'random_bits' : {'var': 0x5F, 'start': 8, 'size': 2},
}

varact2vars_airporttiles = {
    'terrain_type' : {'var': 0x41, 'start': 0, 'size': 8},
    'town_radius_group': {'var': 0x42, 'start': 0, 'size': 3},
    'relative_x': {'var': 0x43, 'start': 0, 'size': 8},
    'relative_y': {'var': 0x43, 'start': 8, 'size': 8},
    'relative_pos': {'var': 0x43, 'start': 0, 'size': 16},
    'animation_frame': {'var': 0x44, 'start': 0, 'size': 8},
}

varact2vars60x_airporttiles = {
    'nearby_tile_slope'            : {'var': 0x60, 'start':  0, 'size':  5, 'function': signed_tile_offset},
    'nearby_tile_is_same_airport'  : {'var': 0x60, 'start':  8, 'size':  1, 'function': signed_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x60, 'start':  9, 'size':  1, 'function': signed_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x60, 'start': 10, 'size':  3, 'function': signed_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x60, 'start': 13, 'size':  2, 'function': signed_tile_offset},
    'nearby_tile_height'           : {'var': 0x60, 'start': 16, 'size':  8, 'function': signed_tile_offset},
    'nearby_tile_class'            : {'var': 0x60, 'start': 24, 'size':  4, 'function': signed_tile_offset},
    'nearby_tile_animation_frame'  : {'var': 0x61, 'start':  0, 'size':  8, 'function': signed_tile_offset},
    'nearby_tile_airporttile_id'   : {'var': 0x62, 'start':  0, 'size': 16, 'function': signed_tile_offset},
}

varact2vars_towns = {
    'is_city'                        : {'var': 0x40, 'start': 0, 'size': 1},
    'cities_enabled'                 : {'var': 0x40, 'start': 1, 'size': 1, 'function': lambda var, info: expression.Not(var, var.pos)},
    'population'                     : {'var': 0x82, 'start': 0, 'size': 16},
    'has_church'                     : {'var': 0x92, 'start': 1, 'size': 1},
    'has_stadium'                    : {'var': 0x92, 'start': 2, 'size': 1},
    'town_zone_0_radius_square'      : {'var': 0x94, 'start': 0, 'size': 16},
    'town_zone_1_radius_square'      : {'var': 0x96, 'start': 0, 'size': 16},
    'town_zone_2_radius_square'      : {'var': 0x98, 'start': 0, 'size': 16},
    'town_zone_3_radius_square'      : {'var': 0x9A, 'start': 0, 'size': 16},
    'town_zone_4_radius_square'      : {'var': 0x9C, 'start': 0, 'size': 16},
    'num_houses'                     : {'var': 0xB6, 'start': 0, 'size': 16},
    'percent_transported_passengers' : {'var': 0xCA, 'start': 0, 'size': 8, 'function': lambda var, info: muldiv(var, 101, 256)},
    'percent_transported_mail'       : {'var': 0xCB, 'start': 0, 'size': 8, 'function': lambda var, info: muldiv(var, 101, 256)},
}


varact2vars[0x00] = varact2vars_trains
varact2vars60x[0x00] = varact2vars60x_vehicles
varact2vars[0x01] = varact2vars_roadvehs
varact2vars60x[0x01] = varact2vars60x_vehicles
varact2vars[0x02] = varact2vars_ships
varact2vars60x[0x02] = varact2vars60x_vehicles
varact2vars[0x03] = varact2vars_aircraft
varact2vars60x[0x03] = varact2vars60x_vehicles
varact2vars[0x05] = varact2vars_canals
varact2vars[0x09] = varact2vars_industrytiles
varact2vars60x[0x09] = varact2vars60x_industrytiles
varact2vars[0x0A] = varact2vars_industries
varact2vars60x[0x0A] = varact2vars60x_industries
varact2vars[0x0D] = varact2vars_airports
varact2vars[0x0F] = varact2vars_objects
varact2vars60x[0x0F] = varact2vars60x_objects
varact2vars[0x10] = varact2vars_railtype
varact2vars[0x11] = varact2vars_airporttiles
varact2vars60x[0x11] = varact2vars60x_airporttiles
varact2vars[0x12] = varact2vars_towns
