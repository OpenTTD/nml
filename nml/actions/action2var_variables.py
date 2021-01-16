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

# Use feature 0x14 for towns (accessible via station/house/industry parent scope)
varact2vars = 0x15 * [{}]
varact2vars60x = 0x15 * [{}]
# feature number:      0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x14, None, 0x14, 0x14, None, 0x0A, 0x14, None, None, None, None, 0x14, None, None, None, None]

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
        raise generic.ScriptError("'{}'() requires one argument, encountered {:d}".format(name, len(args)), pos)
    return (args[0], [])

# Some commonly used functions that apply some modification to the raw variable value
# To pass extra parameters, lambda calculus may be used

def value_sign_extend(var, info):
    #r = (x ^ m) - m; with m being (1 << (num_bits -1))
    m = expression.ConstantNumeric(1 << (info['size'] - 1))
    return nmlop.SUB(nmlop.XOR(var, m), m)

def value_mul_div(mul, div):
    return lambda var, info: nmlop.DIV(nmlop.MUL(var, mul), div)

def value_add_constant(const):
    return lambda var, info: nmlop.ADD(var, const)

def value_equals(const):
    return lambda var, info: nmlop.CMP_EQ(var, const)

# Commonly used functions to let a variable accept an (x, y)-offset as parameters

def tile_offset(name, args, pos, info, min, max):
    if len(args) != 2:
        raise generic.ScriptError("'{}'() requires 2 arguments, encountered {:d}".format(name, len(args)), pos)
    for arg in args:
        if isinstance(arg, expression.ConstantNumeric):
            generic.check_range(arg.value, min, max, "Argument of '{}'".format(name), arg.pos)

    x = nmlop.AND(args[0], 0xF)
    y = nmlop.AND(args[1], 0xF)
    # Shift y left by four
    y = nmlop.SHIFT_LEFT(y, 4)
    param = nmlop.ADD(x, y)
    #Make sure to reduce the result
    return ( param.reduce(), [] )

def signed_tile_offset(name, args, pos, info):
    return tile_offset(name, args, pos, info, -8, 7)

def unsigned_tile_offset(name, args, pos, info):
    return tile_offset(name, args, pos, info, 0, 15)

#
# Global variables, usable for all features
#

varact2_globalvars = {
    'current_month'        : {'var': 0x02, 'start':  0, 'size':  8},
    'current_day_of_month' : {'var': 0x02, 'start':  8, 'size':  5},
    'is_leapyear'          : {'var': 0x02, 'start': 15, 'size':  1},
    'current_day_of_year'  : {'var': 0x02, 'start': 16, 'size':  9},
    'traffic_side'         : {'var': 0x06, 'start':  4, 'size':  1},
    'animation_counter'    : {'var': 0x0A, 'start':  0, 'size': 16},
    'current_callback'     : {'var': 0x0C, 'start':  0, 'size': 16},
    'extra_callback_info1' : {'var': 0x10, 'start':  0, 'size': 32},
    'game_mode'            : {'var': 0x12, 'start':  0, 'size':  8},
    'extra_callback_info2' : {'var': 0x18, 'start':  0, 'size': 32},
    'display_options'      : {'var': 0x1B, 'start':  0, 'size':  6},
    'last_computed_result' : {'var': 0x1C, 'start':  0, 'size': 32},
    'snowline_height'      : {'var': 0x20, 'start':  0, 'size':  8},
    'difficulty_level'     : {'var': 0x22, 'start':  0, 'size':  8},
    'current_date'         : {'var': 0x23, 'start':  0, 'size': 32},
    'current_year'         : {'var': 0x24, 'start':  0, 'size': 32},
}

#
# Vehicles (features 0x00 - 0x03)
# A few variables have an implementation that differs per vehicle type
# These are to be found below
#

varact2vars_vehicles = {
    'grfid'                            : {'var': 0x25, 'start':  0, 'size': 32},
    'position_in_consist'              : {'var': 0x40, 'start':  0, 'size':  8},
    'position_in_consist_from_end'     : {'var': 0x40, 'start':  8, 'size':  8},
    'num_vehs_in_consist'              : {'var': 0x40, 'start': 16, 'size':  8, 'value_function': value_add_constant(1)}, # Zero-based, add 1 to make sane
    'position_in_vehid_chain'          : {'var': 0x41, 'start':  0, 'size':  8},
    'position_in_vehid_chain_from_end' : {'var': 0x41, 'start':  8, 'size':  8},
    'num_vehs_in_vehid_chain'          : {'var': 0x41, 'start': 16, 'size':  8}, # One-based, already sane
    'cargo_classes_in_consist'         : {'var': 0x42, 'start':  0, 'size':  8},
    'most_common_cargo_type'           : {'var': 0x42, 'start':  8, 'size':  8},
    'most_common_cargo_subtype'        : {'var': 0x42, 'start': 16, 'size':  8},
    'bitmask_consist_info'             : {'var': 0x42, 'start': 24, 'size':  8},
    'company_num'                      : {'var': 0x43, 'start':  0, 'size':  8},
    'company_type'                     : {'var': 0x43, 'start': 16, 'size':  2},
    'company_colour1'                  : {'var': 0x43, 'start': 24, 'size':  4},
    'company_colour2'                  : {'var': 0x43, 'start': 28, 'size':  4},
    'aircraft_height'                  : {'var': 0x44, 'start':  8, 'size':  8},
    'airport_type'                     : {'var': 0x44, 'start':  0, 'size':  8},
    'curv_info_prev_cur'               : {'var': 0x45, 'start':  0, 'size':  4, 'value_function': value_sign_extend},
    'curv_info_cur_next'               : {'var': 0x45, 'start':  8, 'size':  4, 'value_function': value_sign_extend},
    'curv_info_prev_next'              : {'var': 0x45, 'start': 16, 'size':  4, 'value_function': value_sign_extend},
    'curv_info'                        : {'var': 0x45, 'start':  0, 'size': 12,
            'value_function': lambda var, info: nmlop.AND(var, 0x0F0F).reduce()},
    'motion_counter'                   : {'var': 0x46, 'start':  8, 'size': 24},
    'cargo_type_in_veh'                : {'var': 0x47, 'start':  0, 'size':  8},
    'cargo_unit_weight'                : {'var': 0x47, 'start':  8, 'size':  8},
    'cargo_classes'                    : {'var': 0x47, 'start': 16, 'size': 16},
    'vehicle_is_available'             : {'var': 0x48, 'start':  0, 'size':  1},
    'vehicle_is_testing'               : {'var': 0x48, 'start':  1, 'size':  1},
    'vehicle_is_offered'               : {'var': 0x48, 'start':  2, 'size':  1},
    'build_year'                       : {'var': 0x49, 'start':  0, 'size': 32},
    'vehicle_is_potentially_powered'   : {'var': 0x4A, 'start':  8, 'size':  1},
    'tile_has_catenary'                : {'var': 0x4A, 'start':  9, 'size':  1},
    'date_of_last_service'             : {'var': 0x4B, 'start':  0, 'size': 32},
    'position_in_articulated_veh'          : {'var': 0x4D, 'start':  0, 'size':  8},
    'position_in_articulated_veh_from_end' : {'var': 0x4D, 'start':  8, 'size':  8},
    'waiting_triggers'                 : {'var': 0x5F, 'start':  0, 'size':  8},
    'random_bits'                      : {'var': 0x5F, 'start':  8, 'size':  8},
    'direction'                        : {'var': 0x9F, 'start':  0, 'size':  8},
    'vehicle_is_hidden'                : {'var': 0xB2, 'start':  0, 'size':  1},
    'vehicle_is_stopped'               : {'var': 0xB2, 'start':  1, 'size':  1},
    'vehicle_is_crashed'               : {'var': 0xB2, 'start':  7, 'size':  1},
    'cargo_capacity'                   : {'var': 0xBA, 'start':  0, 'size': 16},
    'cargo_count'                      : {'var': 0xBC, 'start':  0, 'size': 16},
    'age_in_days'                      : {'var': 0xC0, 'start':  0, 'size': 16},
    'max_age_in_days'                  : {'var': 0xC2, 'start':  0, 'size': 16},
    'vehicle_type_id'                  : {'var': 0xC6, 'start':  0, 'size': 16},
    'vehicle_is_flipped'               : {'var': 0xC8, 'start':  1, 'size':  1},
    'breakdowns_since_last_service'    : {'var': 0xCA, 'start':  0, 'size':  8},
    'vehicle_is_broken'                : {'var': 0xCB, 'start':  0, 'size':  8, 'value_function': value_equals(1)},
    'reliability'                      : {'var': 0xCE, 'start':  0, 'size': 16, 'value_function': value_mul_div(101, 0x10000)},
    'cargo_subtype'                    : {'var': 0xF2, 'start':  0, 'size':  8},
    'vehicle_is_unloading'             : {'var': 0xFE, 'start':  1, 'size':  1},
    'vehicle_is_powered'               : {'var': 0xFE, 'start':  5, 'size':  1},
    'vehicle_is_not_powered'           : {'var': 0xFE, 'start':  6, 'size':  1},
    'vehicle_is_reversed'              : {'var': 0xFE, 'start':  8, 'size':  1},
    'built_during_preview'             : {'var': 0xFE, 'start': 10, 'size':  1},
}

# Vehicle-type-specific variables

varact2vars_trains = {
    **varact2vars_vehicles,
    #0x4786 / 0x10000 is an approximation of 3.5790976, the conversion factor
    #for train speed
    'max_speed'           : {'var': 0x98, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x4786, 0x10000)},
    'current_speed'       : {'var': 0xB4, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x4786, 0x10000)},
    'current_railtype'    : {'var': 0x4A, 'start':  0, 'size':  8},
    'current_max_speed'   : {'var': 0x4C, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x4786, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 7, 'size':  1},
}

varact2vars_roadvehs = {
    **varact2vars_vehicles,
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for road vehicle speed
    'max_speed'           : {'var': 0x98, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'current_speed'       : {'var': 0xB4, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'current_roadtype'    : {'var': 0x4A, 'start':  0, 'size':  8},
    'current_tramtype'    : {'var': 0x4A, 'start':  0, 'size':  8},
    'current_max_speed'   : {'var': 0x4C, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 0, 'size':  8, 'value_function': value_equals(0xFE)},
}

varact2vars_ships = {
    **varact2vars_vehicles,
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for ship speed
    'max_speed'           : {'var': 0x98, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'current_speed'       : {'var': 0xB4, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'current_max_speed'   : {'var': 0x4C, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x23C3, 0x10000)},
    'vehicle_is_in_depot' : {'var': 0xE2, 'start': 7, 'size':  1},
}

varact2vars_aircraft = {
    **varact2vars_vehicles,
    #0x3939 / 0x1000 is an approximation of 0.279617, the conversion factor
    #Note that the denominator has one less zero here!
    #for aircraft speed
    'max_speed'           : {'var': 0x98, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x3939, 0x1000)},
    'current_speed'       : {'var': 0xB4, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x3939, 0x1000)},
    'current_max_speed'   : {'var': 0x4C, 'start': 0, 'size': 16, 'value_function': value_mul_div(0x3939, 0x1000)},
    'vehicle_is_in_depot' : {'var': 0xE6, 'start': 0, 'size':  8, 'value_function': value_equals(0)},
}

def signed_byte_parameter(name, args, pos, info):
    # Convert to a signed byte by AND-ing with 0xFF
    if len(args) != 1:
        raise generic.ScriptError("{}() requires one argument, encountered {:d}".format(name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):

        generic.check_range(args[0].value, -128, 127, "parameter of {}()".format(name), pos)
    ret = nmlop.AND(args[0], 0xFF, pos).reduce()
    return (ret, [])

def vehicle_railtype(name, args, pos, info):
    return (expression.functioncall.builtin_resolve_typelabel(name, args, pos, table_name="railtype"), [])

def vehicle_roadtype(name, args, pos, info):
    return (expression.functioncall.builtin_resolve_typelabel(name, args, pos, table_name="roadtype"), [])

def vehicle_tramtype(name, args, pos, info):
    return (expression.functioncall.builtin_resolve_typelabel(name, args, pos, table_name="tramtype"), [])

varact2vars60x_vehicles = {
    'count_veh_id'        : {'var': 0x60, 'start':  0, 'size': 8},
    'other_veh_curv_info' : {'var': 0x62, 'start':  0, 'size': 4, 'param_function':signed_byte_parameter, 'value_function':value_sign_extend},
    'other_veh_is_hidden' : {'var': 0x62, 'start':  7, 'size': 1, 'param_function':signed_byte_parameter},
    'other_veh_x_offset'  : {'var': 0x62, 'start':  8, 'size': 8, 'param_function':signed_byte_parameter, 'value_function':value_sign_extend},
    'other_veh_y_offset'  : {'var': 0x62, 'start': 16, 'size': 8, 'param_function':signed_byte_parameter, 'value_function':value_sign_extend},
    'other_veh_z_offset'  : {'var': 0x62, 'start': 24, 'size': 8, 'param_function':signed_byte_parameter, 'value_function':value_sign_extend},
}

varact2vars60x_trains = {
    **varact2vars60x_vehicles,
    # Var 0x63 bit 0 is only useful when testing multiple bits at once. On its own it is already covered by railtype_available().
    'tile_supports_railtype' : {'var': 0x63, 'start':  1, 'size': 1, 'param_function':vehicle_railtype},
    'tile_powers_railtype'   : {'var': 0x63, 'start':  2, 'size': 1, 'param_function':vehicle_railtype},
    'tile_is_railtype'       : {'var': 0x63, 'start':  3, 'size': 1, 'param_function':vehicle_railtype},
}

varact2vars60x_roadvehs = {
    **varact2vars60x_vehicles,
    # Var 0x63 bit 0 is only useful when testing multiple bits at once. On its own it is already covered by road/tramtype_available().
    'tile_supports_roadtype' : {'var': 0x63, 'start':  1, 'size': 1, 'param_function':vehicle_roadtype},
    'tile_supports_tramtype' : {'var': 0x63, 'start':  1, 'size': 1, 'param_function':vehicle_tramtype},
    'tile_powers_roadtype'   : {'var': 0x63, 'start':  2, 'size': 1, 'param_function':vehicle_roadtype},
    'tile_powers_tramtype'   : {'var': 0x63, 'start':  2, 'size': 1, 'param_function':vehicle_tramtype},
    'tile_is_roadtype'       : {'var': 0x63, 'start':  3, 'size': 1, 'param_function':vehicle_roadtype},
    'tile_is_tramtype'       : {'var': 0x63, 'start':  3, 'size': 1, 'param_function':vehicle_tramtype},
}

#
# Stations (feature 0x04)
#

# 'Base station' variables are shared between stations and airports
varact2vars_base_stations = {
    # Var 48 doesn't work with newcargos, do not use
    'had_vehicle_of_type' : {'var': 0x8A, 'start': 1, 'size': 5}, # Only read bits 1-5
    'is_waypoint'         : {'var': 0x8A, 'start': 6, 'size': 1},
    'facilities'          : {'var': 0xF0, 'start': 0, 'size': 8},
    'airport_type'        : {'var': 0xF1, 'start': 0, 'size': 8},
    # Variables F2, F3, F6 (roadstop, airport flags) are next to useless
    # Also, their values are not the same as in TTDP / spec
    # Therefore, these are not implemented
    'build_date'          : {'var': 0xFA, 'start': 0, 'size': 16, 'value_function': value_add_constant(701265)}
}

varact2vars60x_base_stations = {
    'cargo_amount_waiting'      : {'var': 0x60, 'start': 0, 'size': 32},
    'cargo_time_since_pickup'   : {'var': 0x61, 'start': 0, 'size': 32},
    'cargo_rating'              : {'var': 0x62, 'start': 0, 'size': 32, 'value_function': value_mul_div(101, 256)},
    'cargo_time_en_route'       : {'var': 0x63, 'start': 0, 'size': 32},
    'cargo_last_vehicle_speed'  : {'var': 0x64, 'start': 0, 'size':  8},
    'cargo_last_vehicle_age'    : {'var': 0x64, 'start': 8, 'size':  8},
    'cargo_accepted'            : {'var': 0x65, 'start': 3, 'size':  1},
    'cargo_accepted_ever'       : {'var': 0x69, 'start': 0, 'size':  1},
    'cargo_accepted_last_month' : {'var': 0x69, 'start': 1, 'size':  1},
    'cargo_accepted_this_month' : {'var': 0x69, 'start': 2, 'size':  1},
    'cargo_accepted_bigtick'    : {'var': 0x69, 'start': 3, 'size':  1},
}

varact2vars_stations = {
    **varact2vars_base_stations,
    # Vars 40, 41, 46, 47, 49 are implemented as 60+x vars,
    # except for the 'tile type' part which is always the same anyways
    'tile_type'                : {'var': 0x40, 'start': 24, 'size': 4},
    'terrain_type'             : {'var': 0x42, 'start':  0, 'size': 8},
    'track_type'               : {'var': 0x42, 'start':  8, 'size': 8},
    'company_num'              : {'var': 0x43, 'start':  0, 'size': 8},
    'company_type'             : {'var': 0x43, 'start': 16, 'size': 2},
    'company_colour1'          : {'var': 0x43, 'start': 24, 'size': 4},
    'company_colour2'          : {'var': 0x43, 'start': 28, 'size': 4},
    'pbs_reserved'             : {'var': 0x44, 'start':  0, 'size': 1},
    'pbs_reserved_or_disabled' : {'var': 0x44, 'start':  1, 'size': 1},
    'pbs_enabled'              : {'var': 0x44, 'start':  2, 'size': 1},
    'rail_continuation'        : {'var': 0x45, 'start':  0, 'size': 8},
    'rail_present'             : {'var': 0x45, 'start':  8, 'size': 8},
    'animation_frame'          : {'var': 0x4A, 'start':  0, 'size': 8},
}

# Mapping of param values for platform_xx vars to variable numbers
mapping_platform_param = {
    (0, False) : 0x40,
    (1, False) : 0x41,
    (0, True)  : 0x46,
    (1, True)  : 0x47,
    (2, False) : 0x49,
}

def platform_info_param(name, args, pos, info):
    if len(args) != 1:
        raise generic.ScriptError("'{}'() requires one argument, encountered {:d}".format(name, len(args)), pos)
    if (not isinstance(args[0], expression.ConstantNumeric)) or args[0].value not in (0, 1, 2):
        raise generic.ScriptError("Invalid argument for '{}'(), must be one of PLATFORM_SAME_XXX.".format(name), pos)

    is_middle = 'middle' in info and info['middle']
    if is_middle and args[0].value == 2:
        raise generic.ScriptError("Invalid argument for '{}'(), PLATFORM_SAME_DIRECTION is not supported here.".format(name), pos)
    # Temporarily store variable number in the param, this will be fixed in the value_function
    return (expression.ConstantNumeric(mapping_platform_param[(args[0].value, is_middle)]), [])

def platform_info_fix_var(var, info):
    # Variable to use was temporarily stored in the param
    # Fix this now
    var.num = var.param
    var.param = None
    return var

varact2vars60x_stations = {
    **varact2vars60x_base_stations,
    'nearby_tile_animation_frame'   : {'var': 0x66, 'start':  0, 'size': 32, 'param_function': signed_tile_offset},
    'nearby_tile_slope'             : {'var': 0x67, 'start':  0, 'size':  5, 'param_function': signed_tile_offset},
    'nearby_tile_is_water'          : {'var': 0x67, 'start':  9, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_terrain_type'      : {'var': 0x67, 'start': 10, 'size':  3, 'param_function': signed_tile_offset},
    'nearby_tile_water_class'       : {'var': 0x67, 'start': 13, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_height'            : {'var': 0x67, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_class'             : {'var': 0x67, 'start': 24, 'size':  4, 'param_function': signed_tile_offset},
    'nearby_tile_is_station'        : {'var': 0x68, 'start':  0, 'size': 32, 'param_function': signed_tile_offset, 'value_function': lambda var, info: nmlop.CMP_NEQ(var, 0xFFFFFFFF)},
    'nearby_tile_station_id'        : {'var': 0x68, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_same_grf'          : {'var': 0x68, 'start':  8, 'size':  2, 'param_function': signed_tile_offset, 'value_function': value_equals(0)},
    'nearby_tile_other_grf'         : {'var': 0x68, 'start':  8, 'size':  2, 'param_function': signed_tile_offset, 'value_function': value_equals(1)},
    'nearby_tile_original_gfx'      : {'var': 0x68, 'start':  8, 'size':  2, 'param_function': signed_tile_offset, 'value_function': value_equals(2)},
    'nearby_tile_same_station'      : {'var': 0x68, 'start': 10, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_perpendicular'     : {'var': 0x68, 'start': 11, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_platform_type'     : {'var': 0x68, 'start': 12, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_grfid'             : {'var': 0x6A, 'start':  0, 'size': 32, 'param_function': signed_tile_offset},
    # 'var' will be set in the value_function, depending on parameter
    'platform_length'               : {'var': 0x00, 'start': 16, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_count'                : {'var': 0x00, 'start': 20, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_position_from_start'  : {'var': 0x00, 'start':  0, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_position_from_end'    : {'var': 0x00, 'start':  4, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_number_from_start'    : {'var': 0x00, 'start':  8, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_number_from_end'      : {'var': 0x00, 'start': 12, 'size':  4, 'param_function': platform_info_param, 'value_function': platform_info_fix_var},
    'platform_position_from_middle' : {'var': 0x00, 'start':  0, 'size':  4, 'param_function': platform_info_param, 'middle': True, # 'middle' is used by platform_info_param
                                            'value_function': lambda var, info: value_sign_extend(platform_info_fix_var(var, info), info)},
    'platform_number_from_middle'   : {'var': 0x00, 'start':  4, 'size':  4, 'param_function': platform_info_param, 'middle': True, # 'middle' is used by platform_info_param
                                            'value_function': lambda var, info: value_sign_extend(platform_info_fix_var(var, info), info)},
}

#
# Canals (feature 0x05)
#

varact2vars_canals = {
    'tile_height'  : {'var': 0x80, 'start': 0, 'size': 8},
    'terrain_type' : {'var': 0x81, 'start': 0, 'size': 8},
    'dike_map'     : {'var': 0x82, 'start': 0, 'size': 8},
    'random_bits'  : {'var': 0x83, 'start': 0, 'size': 8},
}
# Canals have no 60+X variables

#
# Bridges (feature 0x06) have no variational action2
#

#
# Houses (feature 0x07)
#

def house_same_class(var, info):
    # Just using var 44 fails for non-north house tiles, as these have no class
    # Therefore work around it using var 61
    # Load ID of the north tile from register FF bits 24..31, and use that as param for var 61
    north_tile = expression.Variable(expression.ConstantNumeric(0x7D), expression.ConstantNumeric(24),
                                     expression.ConstantNumeric(0xFF), expression.ConstantNumeric(0xFF), var.pos)
    var61 = expression.Variable(expression.ConstantNumeric(0x7B), expression.ConstantNumeric(info['start']),
                                     expression.ConstantNumeric((1 << info['size']) - 1), expression.ConstantNumeric(0x61), var.pos)
    return nmlop.VAL2(north_tile, var61, var.pos)


varact2vars_houses = {
    'construction_state'    : {'var': 0x40, 'start':  0, 'size':  2},
    'pseudo_random_bits'    : {'var': 0x40, 'start':  2, 'size':  2},
    'age'                   : {'var': 0x41, 'start':  0, 'size':  8},
    'town_zone'             : {'var': 0x42, 'start':  0, 'size':  8},
    'terrain_type'          : {'var': 0x43, 'start':  0, 'size':  8},
    'same_house_count_town' : {'var': 0x44, 'start':  0, 'size':  8},
    'same_house_count_map'  : {'var': 0x44, 'start':  8, 'size':  8},
    'same_class_count_town' : {'var': 0xFF, 'start': 16, 'size':  8, 'value_function': house_same_class}, # 'var' is unused
    'same_class_count_map'  : {'var': 0xFF, 'start': 24, 'size':  8, 'value_function': house_same_class}, # 'var' is unused
    'generating_town'       : {'var': 0x45, 'start':  0, 'size':  1},
    'animation_frame'       : {'var': 0x46, 'start':  0, 'size':  8},
    'x_coordinate'          : {'var': 0x47, 'start':  0, 'size': 16},
    'y_coordinate'          : {'var': 0x47, 'start': 16, 'size': 16},
    'random_bits'           : {'var': 0x5F, 'start':  8, 'size':  8},
    'relative_x'            : {'var': 0x7D, 'start':  0, 'size':  8, 'param': 0xFF},
    'relative_y'            : {'var': 0x7D, 'start':  8, 'size':  8, 'param': 0xFF},
    'relative_pos'          : {'var': 0x7D, 'start':  0, 'size': 16, 'param': 0xFF},
    'house_tile'            : {'var': 0x7D, 'start': 16, 'size':  8, 'param': 0xFF},
    'house_type_id'         : {'var': 0x7D, 'start': 24, 'size':  8, 'param': 0xFF},
}

def cargo_accepted_nearby(name, args, pos, info):
    # cargo_accepted_nearby(cargo[, xoffset, yoffset])
    if len(args) not in (1, 3):
        raise generic.ScriptError("{}() requires 1 or 3 arguments, encountered {:d}".format(name, len(args)), pos)

    if len(args) > 1:
        offsets = args[1:3]
        for i, offs in enumerate(offsets[:]):
            if isinstance(offs, expression.ConstantNumeric):
                generic.check_range(offs.value, -128, 127, "{}-parameter {:d} '{}offset'".format(name, i + 1, "x" if i == 0 else "y"), pos)
            offsets[i] = nmlop.AND(offs, 0xFF, pos).reduce()
        # Register 0x100 should be set to xoffset | (yoffset << 8)
        reg100 = nmlop.OR(nmlop.MUL(offsets[1], 256, pos), offsets[0]).reduce()
    else:
        reg100 = expression.ConstantNumeric(0, pos)

    return (args[0], [(0x100, reg100)])

def nearest_house_matching_criterion(name, args, pos, info):
    # nearest_house_matching_criterion(radius, criterion)
    # parameter is radius | (criterion << 6)
    if len(args) != 2:
        raise generic.ScriptError("{}() requires 2 arguments, encountered {:d}".format(name, len(args)), pos)
    if isinstance(args[0], expression.ConstantNumeric):
        generic.check_range(args[0].value, 1, 63, "{}()-parameter 1 'radius'".format(name), pos)
    if isinstance(args[1], expression.ConstantNumeric) and args[1].value not in (0, 1, 2):
        raise generic.ScriptError("Invalid value for {}()-parameter 2 'criterion'".format(name), pos)

    radius = nmlop.AND(args[0], 0x3F, pos)
    criterion = nmlop.AND(args[1], 0x03, pos)
    criterion = nmlop.MUL(criterion, 0x40)
    retval = nmlop.OR(criterion, radius).reduce()
    return (retval, [])

varact2vars60x_houses = {
    'old_house_count_town'               : {'var': 0x60, 'start':  0, 'size':  8},
    'old_house_count_map'                : {'var': 0x60, 'start':  8, 'size':  8},
    'other_house_count_town'             : {'var': 0x61, 'start':  0, 'size':  8},
    'other_house_count_map'              : {'var': 0x61, 'start':  8, 'size':  8},
    'other_class_count_town'             : {'var': 0x61, 'start': 16, 'size':  8},
    'other_class_count_map'              : {'var': 0x61, 'start': 24, 'size':  8},
    'nearby_tile_slope'                  : {'var': 0x62, 'start':  0, 'size':  5, 'param_function': signed_tile_offset},
    'nearby_tile_is_water'               : {'var': 0x62, 'start':  9, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_terrain_type'           : {'var': 0x62, 'start': 10, 'size':  3, 'param_function': signed_tile_offset},
    'nearby_tile_water_class'            : {'var': 0x62, 'start': 13, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_height'                 : {'var': 0x62, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_class'                  : {'var': 0x62, 'start': 24, 'size':  4, 'param_function': signed_tile_offset},
    'nearby_tile_animation_frame'        : {'var': 0x63, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},
    'cargo_accepted_nearby_ever'         : {'var': 0x64, 'start':  0, 'size':  1, 'param_function': cargo_accepted_nearby},
    'cargo_accepted_nearby_last_month'   : {'var': 0x64, 'start':  1, 'size':  1, 'param_function': cargo_accepted_nearby},
    'cargo_accepted_nearby_this_month'   : {'var': 0x64, 'start':  2, 'size':  1, 'param_function': cargo_accepted_nearby},
    'cargo_accepted_nearby_last_bigtick' : {'var': 0x64, 'start':  3, 'size':  1, 'param_function': cargo_accepted_nearby},
    'cargo_accepted_nearby_watched'      : {'var': 0x64, 'start':  4, 'size':  1, 'param_function': cargo_accepted_nearby},
    'nearest_house_matching_criterion'   : {'var': 0x65, 'start':  0, 'size':  8, 'param_function': nearest_house_matching_criterion},
    'nearby_tile_house_id'               : {'var': 0x66, 'start':  0, 'size': 16, 'param_function': signed_tile_offset, 'value_function': value_sign_extend},
    'nearby_tile_house_class'            : {'var': 0x66, 'start': 16, 'size': 16, 'param_function': signed_tile_offset, 'value_function': value_sign_extend},
    'nearby_tile_house_grfid'            : {'var': 0x67, 'start':  0, 'size': 32, 'param_function': signed_tile_offset},
}

#
# Global variables (feature 0x08) have no variational action2
#

#
# Industry tiles (feature 0x09)
#

varact2vars_industrytiles = {
    'construction_state' : {'var': 0x40, 'start': 0, 'size':  2},
    'terrain_type'       : {'var': 0x41, 'start': 0, 'size':  8},
    'town_zone'          : {'var': 0x42, 'start': 0, 'size':  3},
    'relative_x'         : {'var': 0x43, 'start': 0, 'size':  8},
    'relative_y'         : {'var': 0x43, 'start': 8, 'size':  8},
    'relative_pos'       : {'var': 0x43, 'start': 0, 'size': 16},
    'animation_frame'    : {'var': 0x44, 'start': 0, 'size':  8},
    'random_bits'        : {'var': 0x5F, 'start': 8, 'size':  8},
}

varact2vars60x_industrytiles = {
    'nearby_tile_slope'            : {'var': 0x60, 'start':  0, 'size':  5, 'param_function': signed_tile_offset},
    'nearby_tile_is_same_industry' : {'var': 0x60, 'start':  8, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x60, 'start':  9, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x60, 'start': 10, 'size':  3, 'param_function': signed_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x60, 'start': 13, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_height'           : {'var': 0x60, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_class'            : {'var': 0x60, 'start': 24, 'size':  4, 'param_function': signed_tile_offset},
    'nearby_tile_animation_frame'  : {'var': 0x61, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_industrytile_id'  : {'var': 0x62, 'start':  0, 'size': 16, 'param_function': signed_tile_offset},
}

#
# Industries (feature 0x0A)
#

varact2vars_industries = {
    'waiting_cargo_1'              : {'var': 0x40, 'start':  0, 'size': 16, 'replaced_by': 'incoming_cargo_waiting'},
    'waiting_cargo_2'              : {'var': 0x41, 'start':  0, 'size': 16, 'replaced_by': 'incoming_cargo_waiting'},
    'waiting_cargo_3'              : {'var': 0x42, 'start':  0, 'size': 16, 'replaced_by': 'incoming_cargo_waiting'},
    'water_distance'               : {'var': 0x43, 'start':  0, 'size': 32},
    'layout_num'                   : {'var': 0x44, 'start':  0, 'size':  8},
    # bits 0 .. 16 are either useless or already covered by var A7
    'founder_type'                 : {'var': 0x45, 'start': 16, 'size':  2},
    'founder_colour1'              : {'var': 0x45, 'start': 24, 'size':  4},
    'founder_colour2'              : {'var': 0x45, 'start': 28, 'size':  4},
    'build_date'                   : {'var': 0x46, 'start':  0, 'size': 32},
    'random_bits'                  : {'var': 0x5F, 'start':  8, 'size': 16},
    'produced_cargo_waiting_1'     : {'var': 0x8A, 'start':  0, 'size': 16, 'replaced_by': 'produced_cargo_waiting'},
    'produced_cargo_waiting_2'     : {'var': 0x8C, 'start':  0, 'size': 16, 'replaced_by': 'produced_cargo_waiting'},
    'production_rate_1'            : {'var': 0x8E, 'start':  0, 'size':  8, 'replaced_by': 'production_rate'},
    'production_rate_2'            : {'var': 0x8F, 'start':  0, 'size':  8, 'replaced_by': 'production_rate'},
    'production_level'             : {'var': 0x93, 'start':  0, 'size':  8},
    'produced_this_month_1'        : {'var': 0x94, 'start':  0, 'size': 16, 'replaced_by': 'this_month_production'},
    'produced_this_month_2'        : {'var': 0x96, 'start':  0, 'size': 16, 'replaced_by': 'this_month_production'},
    'transported_this_month_1'     : {'var': 0x98, 'start':  0, 'size': 16, 'replaced_by': 'this_month_transported'},
    'transported_this_month_2'     : {'var': 0x9A, 'start':  0, 'size': 16, 'replaced_by': 'this_month_transported'},
    'transported_last_month_pct_1' : {'var': 0x9C, 'start':  0, 'size':  8, 'value_function': value_mul_div(101, 256), 'replaced_by': 'transported_last_month_pct'},
    'transported_last_month_pct_2' : {'var': 0x9D, 'start':  0, 'size':  8, 'value_function': value_mul_div(101, 256), 'replaced_by': 'transported_last_month_pct'},
    'produced_last_month_1'        : {'var': 0x9E, 'start':  0, 'size': 16, 'replaced_by': 'last_month_production'},
    'produced_last_month_2'        : {'var': 0xA0, 'start':  0, 'size': 16, 'replaced_by': 'last_month_production'},
    'transported_last_month_1'     : {'var': 0xA2, 'start':  0, 'size': 16, 'replaced_by': 'last_month_transported'},
    'transported_last_month_2'     : {'var': 0xA4, 'start':  0, 'size': 16, 'replaced_by': 'last_month_transported'},
    'founder'                      : {'var': 0xA7, 'start':  0, 'size':  8},
    'colour'                       : {'var': 0xA8, 'start':  0, 'size':  8},
    'counter'                      : {'var': 0xAA, 'start':  0, 'size': 16},
    'build_type'                   : {'var': 0xB3, 'start':  0, 'size':  2},
    'last_accept_date'             : {'var': 0xB4, 'start':  0, 'size': 16, 'value_function': value_add_constant(701265)},
}

def industry_count(name, args, pos, info):
    if len(args) < 1 or len(args) > 2:
        raise generic.ScriptError("'{}'() requires between 1 and 2 argument(s), encountered {:d}".format(name, len(args)), pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 1 else args[1]
    extra_params = [(0x100, grfid)]

    return (args[0], extra_params)


def industry_layout_count(name, args, pos, info):
    if len(args) < 2 or len(args) > 3:
        raise generic.ScriptError("'{}'() requires between 2 and 3 argument(s), encountered {:d}".format(name, len(args)), pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 2 else args[2]

    extra_params = []
    extra_params.append( (0x100, grfid) )
    extra_params.append( (0x101, nmlop.AND(args[1], 0xFF).reduce()) )
    return (args[0], extra_params)

def industry_town_count(name, args, pos, info):
    if len(args) < 1 or len(args) > 2:
        raise generic.ScriptError("'{}'() requires between 1 and 2 argument(s), encountered {:d}".format(name, len(args)), pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 1 else args[1]

    extra_params = []
    extra_params.append( (0x100, grfid) )
    extra_params.append( (0x101, expression.ConstantNumeric(0x0100)) )
    return (args[0], extra_params)

def industry_cargotype(name, args, pos, info):
    return (expression.functioncall.builtin_resolve_typelabel(name, args, pos, table_name="cargotype"), [])

varact2vars60x_industries = {
    'nearby_tile_industry_tile_id' : {'var': 0x60, 'start':  0, 'size': 16, 'param_function': unsigned_tile_offset},
    'nearby_tile_random_bits'      : {'var': 0x61, 'start':  0, 'size':  8, 'param_function': unsigned_tile_offset},
    'nearby_tile_slope'            : {'var': 0x62, 'start':  0, 'size':  5, 'param_function': unsigned_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x62, 'start':  9, 'size':  1, 'param_function': unsigned_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x62, 'start': 10, 'size':  3, 'param_function': unsigned_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x62, 'start': 13, 'size':  2, 'param_function': unsigned_tile_offset},
    'nearby_tile_height'           : {'var': 0x62, 'start': 16, 'size':  8, 'param_function': unsigned_tile_offset},
    'nearby_tile_class'            : {'var': 0x62, 'start': 24, 'size':  4, 'param_function': unsigned_tile_offset},
    'nearby_tile_animation_frame'  : {'var': 0x63, 'start':  0, 'size':  8, 'param_function': unsigned_tile_offset},
    'town_manhattan_dist'          : {'var': 0x65, 'start':  0, 'size': 16, 'param_function': signed_tile_offset},
    'town_zone'                    : {'var': 0x65, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'town_euclidean_dist'          : {'var': 0x66, 'start':  0, 'size': 32, 'param_function': signed_tile_offset},
    'industry_count'               : {'var': 0x67, 'start': 16, 'size':  8, 'param_function': industry_count},
    'industry_distance'            : {'var': 0x67, 'start':  0, 'size': 16, 'param_function': industry_count},
    'industry_layout_count'        : {'var': 0x68, 'start': 16, 'size':  8, 'param_function': industry_layout_count},
    'industry_layout_distance'     : {'var': 0x68, 'start':  0, 'size': 16, 'param_function': industry_layout_count},
    'industry_town_count'          : {'var': 0x68, 'start': 16, 'size':  8, 'param_function': industry_town_count},
    'produced_cargo_waiting'       : {'var': 0x69, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'this_month_production'        : {'var': 0x6A, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'this_month_transported'       : {'var': 0x6B, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'last_month_production'        : {'var': 0x6C, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'last_month_transported'       : {'var': 0x6D, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'last_cargo_accepted_at'       : {'var': 0x6E, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'incoming_cargo_waiting'       : {'var': 0x6F, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'production_rate'              : {'var': 0x70, 'start':  0, 'size': 32, 'param_function': industry_cargotype},
    'transported_last_month_pct'   : {'var': 0x71, 'start':  0, 'size': 32, 'param_function': industry_cargotype, 'value_function': value_mul_div(101, 256)},
}

#
# Cargos (feature 0x0B) have no own varaction2 variables
# Sounds (feature 0x0C) have no variational action2
#

#
# Airports (feature 0x0D)
#

varact2vars_airports = {
    **varact2vars_base_stations,
    'layout' : {'var': 0x40, 'start': 0, 'size': 32},
}
varact2vars60x_airports = {
    **varact2vars60x_base_stations,
}

#
# New Signals (feature 0x0E) are not implemented in OpenTTD
#

#
# Objects (feature 0x0F)
#

varact2vars_objects = {
    'relative_x'             : {'var': 0x40, 'start':  0, 'size':  8},
    'relative_y'             : {'var': 0x40, 'start':  8, 'size':  8},
    'relative_pos'           : {'var': 0x40, 'start':  0, 'size': 16},

    'terrain_type'           : {'var': 0x41, 'start':  0, 'size':  3},
    'tile_slope'             : {'var': 0x41, 'start':  8, 'size':  5},

    'build_date'             : {'var': 0x42, 'start':  0, 'size': 32},

    'animation_frame'        : {'var': 0x43, 'start':  0, 'size':  8},
    'company_colour'         : {'var': 0x43, 'start':  0, 'size':  8},

    'owner'                  : {'var': 0x44, 'start':  0, 'size':  8},

    'town_manhattan_dist'    : {'var': 0x45, 'start':  0, 'size': 16},
    'town_zone'              : {'var': 0x45, 'start': 16, 'size':  8},

    'town_euclidean_dist'    : {'var': 0x46, 'start':  0, 'size': 32},
    'view'                   : {'var': 0x48, 'start':  0, 'size':  8},
    'random_bits'            : {'var': 0x5F, 'start':  8, 'size':  8},
}

varact2vars60x_objects = {
    'nearby_tile_object_type'      : {'var': 0x60, 'start':  0, 'size': 16, 'param_function': signed_tile_offset},
    'nearby_tile_object_view'      : {'var': 0x60, 'start': 16, 'size':  4, 'param_function': signed_tile_offset},

    'nearby_tile_random_bits'      : {'var': 0x61, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},

    'nearby_tile_slope'            : {'var': 0x62, 'start':  0, 'size':  5, 'param_function': signed_tile_offset},
    'nearby_tile_is_same_object'   : {'var': 0x62, 'start':  8, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x62, 'start':  9, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x62, 'start': 10, 'size':  3, 'param_function': signed_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x62, 'start': 13, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_height'           : {'var': 0x62, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_class'            : {'var': 0x62, 'start': 24, 'size':  4, 'param_function': signed_tile_offset},

    'nearby_tile_animation_frame'  : {'var': 0x63, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},

    'object_count'                 : {'var': 0x64, 'start': 16, 'size':  8, 'param_function': industry_count},
    'object_distance'              : {'var': 0x64, 'start':  0, 'size': 16, 'param_function': industry_count},
}

#
# Railtypes (feature 0x10)
#

varact2vars_railtype = {
    'terrain_type'          : {'var': 0x40, 'start': 0, 'size':  8},
    'enhanced_tunnels'      : {'var': 0x41, 'start': 0, 'size':  8},
    'level_crossing_status' : {'var': 0x42, 'start': 0, 'size':  8},
    'build_date'            : {'var': 0x43, 'start': 0, 'size': 32},
    'town_zone'             : {'var': 0x44, 'start': 0, 'size':  8},
    'random_bits'           : {'var': 0x5F, 'start': 8, 'size':  2},
}
# Railtypes have no 60+x variables

#
# Airport tiles (feature 0x11)
#

varact2vars_airporttiles = {
    'terrain_type'      : {'var': 0x41, 'start': 0, 'size':  8},
    'town_radius_group' : {'var': 0x42, 'start': 0, 'size':  3},
    'relative_x'        : {'var': 0x43, 'start': 0, 'size':  8},
    'relative_y'        : {'var': 0x43, 'start': 8, 'size':  8},
    'relative_pos'      : {'var': 0x43, 'start': 0, 'size': 16},
    'animation_frame'   : {'var': 0x44, 'start': 0, 'size':  8},
}

varact2vars60x_airporttiles = {
    'nearby_tile_slope'            : {'var': 0x60, 'start':  0, 'size':  5, 'param_function': signed_tile_offset},
    'nearby_tile_is_same_airport'  : {'var': 0x60, 'start':  8, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_is_water'         : {'var': 0x60, 'start':  9, 'size':  1, 'param_function': signed_tile_offset},
    'nearby_tile_terrain_type'     : {'var': 0x60, 'start': 10, 'size':  3, 'param_function': signed_tile_offset},
    'nearby_tile_water_class'      : {'var': 0x60, 'start': 13, 'size':  2, 'param_function': signed_tile_offset},
    'nearby_tile_height'           : {'var': 0x60, 'start': 16, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_class'            : {'var': 0x60, 'start': 24, 'size':  4, 'param_function': signed_tile_offset},
    'nearby_tile_animation_frame'  : {'var': 0x61, 'start':  0, 'size':  8, 'param_function': signed_tile_offset},
    'nearby_tile_airporttile_id'   : {'var': 0x62, 'start':  0, 'size': 16, 'param_function': signed_tile_offset},
}

#
# Roadtypes (feature 0x12)
#

varact2vars_roadtype = {
    'terrain_type'          : {'var': 0x40, 'start': 0, 'size':  8},
    'enhanced_tunnels'      : {'var': 0x41, 'start': 0, 'size':  8},
    'level_crossing_status' : {'var': 0x42, 'start': 0, 'size':  8},
    'build_date'            : {'var': 0x43, 'start': 0, 'size': 32},
    'town_zone'             : {'var': 0x44, 'start': 0, 'size':  8},
    'random_bits'           : {'var': 0x5F, 'start': 8, 'size':  2},
}
# Roadtypes have no 60+x variables

#
# Tramtypes (feature 0x13)
#

varact2vars_tramtype = {
    'terrain_type'          : {'var': 0x40, 'start': 0, 'size':  8},
    'enhanced_tunnels'      : {'var': 0x41, 'start': 0, 'size':  8},
    'level_crossing_status' : {'var': 0x42, 'start': 0, 'size':  8},
    'build_date'            : {'var': 0x43, 'start': 0, 'size': 32},
    'town_zone'             : {'var': 0x44, 'start': 0, 'size':  8},
    'random_bits'           : {'var': 0x5F, 'start': 8, 'size':  2},
}
# Tramtypes have no 60+x variables


#
# Towns are not a true feature, but accessible via the parent scope of e.g. industries, stations
#

varact2vars_towns = {
    'is_city'                        : {'var': 0x40, 'start': 0, 'size': 1},
    'cities_enabled'                 : {'var': 0x40, 'start': 1, 'size': 1, 'value_function': lambda var, info: expression.Not(var, var.pos)},
    'population'                     : {'var': 0x82, 'start': 0, 'size': 16},
    'has_church'                     : {'var': 0x92, 'start': 1, 'size': 1},
    'has_stadium'                    : {'var': 0x92, 'start': 2, 'size': 1},
    'town_zone_0_radius_square'      : {'var': 0x94, 'start': 0, 'size': 16},
    'town_zone_1_radius_square'      : {'var': 0x96, 'start': 0, 'size': 16},
    'town_zone_2_radius_square'      : {'var': 0x98, 'start': 0, 'size': 16},
    'town_zone_3_radius_square'      : {'var': 0x9A, 'start': 0, 'size': 16},
    'town_zone_4_radius_square'      : {'var': 0x9C, 'start': 0, 'size': 16},
    'num_houses'                     : {'var': 0xB6, 'start': 0, 'size': 16},
    'percent_transported_passengers' : {'var': 0xCA, 'start': 0, 'size': 8, 'value_function': value_mul_div(101, 256)},
    'percent_transported_mail'       : {'var': 0xCB, 'start': 0, 'size': 8, 'value_function': value_mul_div(101, 256)},
}


varact2vars[0x00] = varact2vars_trains
varact2vars60x[0x00] = varact2vars60x_trains
varact2vars[0x01] = varact2vars_roadvehs
varact2vars60x[0x01] = varact2vars60x_roadvehs
varact2vars[0x02] = varact2vars_ships
varact2vars60x[0x02] = varact2vars60x_vehicles
varact2vars[0x03] = varact2vars_aircraft
varact2vars60x[0x03] = varact2vars60x_vehicles
varact2vars[0x04] = varact2vars_stations
varact2vars60x[0x04] = varact2vars60x_stations
varact2vars[0x05] = varact2vars_canals
varact2vars[0x07] = varact2vars_houses
varact2vars60x[0x07] = varact2vars60x_houses
varact2vars[0x09] = varact2vars_industrytiles
varact2vars60x[0x09] = varact2vars60x_industrytiles
varact2vars[0x0A] = varact2vars_industries
varact2vars60x[0x0A] = varact2vars60x_industries
varact2vars[0x0D] = varact2vars_airports
varact2vars60x[0x0D] = varact2vars60x_airports
varact2vars[0x0F] = varact2vars_objects
varact2vars60x[0x0F] = varact2vars60x_objects
varact2vars[0x10] = varact2vars_railtype
varact2vars[0x11] = varact2vars_airporttiles
varact2vars60x[0x11] = varact2vars60x_airporttiles
varact2vars[0x12] = varact2vars_roadtype
varact2vars[0x13] = varact2vars_tramtype
varact2vars[0x14] = varact2vars_towns
