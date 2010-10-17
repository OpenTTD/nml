from nml import expression, nmlop, generic

varact2vars = 0x12 * [{}]
varact2vars60x = 0x12 * [{}]
# feature number:      0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x08, None, 0x08, 0x08, None, 0x0A, 0x08, None, None, None, None, 0x08, None, None]

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
    'extra_callback_info2' : {'var': 0x18, 'start': 0, 'size': 32},
    'display_options' : {'var': 0x1B, 'start': 0, 'size': 6},
    'last_computed_result' : {'var': 0x1C, 'start': 0, 'size': 32},
    'snowline_height' : {'var': 0x20, 'start': 0, 'size': 8},
    'difficulty_level' : {'var': 0x22, 'start': 0, 'size': 8},
    'current_date' : {'var': 0x23, 'start': 0, 'size': 32},
    'current_year' : {'var': 0x24, 'start': 0, 'size': 32},
}

varact2vars_vehicles = {
    'position_in_consist' : {'var': 0x40, 'start': 0, 'size': 8},
    'position_in_consist_from_end' : {'var': 0x40, 'start': 8, 'size': 8},
    'num_vehs_in_consist' : {'var': 0x40, 'start': 16, 'size': 8},
    'position_in_vehid_chain' : {'var': 0x41, 'start': 0, 'size': 8},
    'position_in_vehid_chain_from_end' : {'var': 0x41, 'start': 8, 'size': 8},
    'num_vehs_in_vehid_chain' : {'var': 0x41, 'start': 16, 'size': 8},
    'cargo_classes_in_consist' : {'var': 0x42, 'start': 0, 'size': 8},
    'most_common_refit' : {'var': 0x42, 'start': 16, 'size': 8},
    'bitmask_consist_info' : {'var': 0x42, 'start': 24, 'size': 8},
    'company_num' : {'var': 0x43, 'start': 0, 'size': 8},
    'company_type' : {'var': 0x43, 'start': 16, 'size': 2},
    'company_color1' : {'var': 0x43, 'start': 24, 'size': 4},
    'company_color2' : {'var': 0x43, 'start': 28, 'size': 4},
    'aircraft_height' : {'var': 0x44, 'start': 8, 'size': 8},
    'airport_type' : {'var': 0x44, 'start': 0, 'size': 8},
    'curv_info_prev_cur' : {'var': 0x45, 'start': 0, 'size': 4, 'function': signextend},
    'curv_info_cur_next' : {'var': 0x45, 'start': 8, 'size': 4, 'function': signextend},
    'curv_info_prev_next' : {'var': 0x45, 'start': 16, 'size': 4, 'function': signextend},
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
    'refit_cycle' : {'var': 0xF2, 'start': 0, 'size': 8},
    'vehicle_is_powered' : {'var': 0xFE, 'start': 5, 'size': 1},
    'vehicle_is_not_powered' : {'var': 0xFE, 'start': 6, 'size': 1},
    'vehicle_is_potentially_powered': {'var': 0x4A, 'start': 8, 'size': 1},
    'vehicle_is_reversed' : {'var': 0xFE, 'start': 8, 'size': 1},
    'built_during_preview' : {'var': 0xFE, 'start': 10, 'size': 1},
    'current_railtype' : {'var': 0x4A, 'start': 0, 'size': 8},
    'waiting_triggers' : {'var': 0x5F, 'start': 0, 'size': 8},
    'random_bits' : {'var': 0x5F, 'start': 8, 'size': 8},
    'grfid' : {'var': 0x25, 'start': 0, 'size': 32},
    'vehicle_is_stopped' : {'var': 0xB2, 'start': 1, 'size': 1},
    'vehicle_is_crashed' : {'var': 0xB2, 'start': 7, 'size': 1},
    'vehicle_is_broken' : {'var': 0xCB, 'start': 0, 'size': 8, 'function': lambda var, info: expression.BinOp(nmlop.CMP_EQ, var, expression.ConstantNumeric(1, var.pos), var.pos)},
    'date_of_last_service' : {'var': 0x92, 'start': 0, 'size': 16, 'function': lambda var, info: expression.BinOp(nmlop.ADD, var, expression.ConstantNumeric(701265, var.pos), var.pos)},
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
}
varact2vars_trains.update(varact2vars_vehicles);

varact2vars_roadvehs = {
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for road vehicle speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
}
varact2vars_roadvehs.update(varact2vars_vehicles);

varact2vars_ships = {
    #0x23C3 / 0x10000 is an approximation of 7.1581952, the conversion factor
    #for ship speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x23C3, 0x10000)},
}
varact2vars_ships.update(varact2vars_vehicles);

varact2vars_aircraft = {
    #0x3939 / 0x1000 is an approximation of 0.279617, the conversion factor
    #for aircraft speed
    'max_speed'     : {'var': 0x98, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x3939, 0x1000)},
    'current_speed' : {'var': 0xB4, 'start': 0, 'size': 16, 'function': lambda var, info: muldiv(var, 0x3939, 0x1000)},
}
varact2vars_aircraft.update(varact2vars_vehicles);

varact2vars60x_vehicles = {
    'count_veh_id': {'var': 0x60, 'start': 0, 'size': 8},
}

varact2vars_industrytiles = {
    'construction_state' : {'var': 0x40, 'start': 0, 'size': 2},
    'terrain_type' : {'var': 0x41, 'start': 0, 'size': 8},
    'town_radius_group': {'var': 0x42, 'start': 0, 'size': 3},
    'relative_pos': {'var': 0x43, 'start': 0, 'size': 24},
    'animation_frame': {'var': 0x44, 'start': 0, 'size': 8},
}

varact2vars60x_industrytiles = {
    'tile_slope': {'var': 0x60, 'start': 0, 'size': 5, 'tile': 's'},
    'tile_is_same_industry': {'var': 0x60, 'start': 8, 'size': 1, 'tile': 's'},
    'tile_has_water': {'var': 0x60, 'start': 9, 'size': 1, 'tile': 's'},
    'terrain_type_nearby_tile': {'var': 0x60, 'start': 10, 'size': 3, 'tile': 's'},
    'tile_lowest_corner_height': {'var': 0x60, 'start': 16, 'size': 8, 'tile': 's'},
    'animation_frame_nearby_tile': {'var': 0x61, 'start': 0, 'size': 8, 'tile': 's'},
    'industrytile_id_nearby_tile': {'var': 0x62, 'start': 0, 'size': 16, 'tile': 's'},
}

varact2vars_industries = {
    'waiting_cargo_1' : {'var': 0x40, 'start': 0, 'size': 16},
    'waiting_cargo_2' : {'var': 0x41, 'start': 0, 'size': 16},
    'waiting_cargo_3' : {'var': 0x42, 'start': 0, 'size': 16},
    'water_distance' : {'var': 0x43, 'start': 0, 'size': 32},
    'layout_num' : {'var': 0x44, 'start': 0, 'size': 8},
    'company_num' : {'var': 0x45, 'start': 0, 'size': 8},
    'company_type' : {'var': 0x45, 'start': 16, 'size': 2},
    'company_color1' : {'var': 0x45, 'start': 24, 'size': 4},
    'company_color2' : {'var': 0x45, 'start': 28, 'size': 4},
    'build_date' : {'var': 0x46, 'start': 0, 'size': 32},
    'founder' : {'var': 0xA7, 'start': 0, 'size': 8},
    'build_type' : {'var': 0xB3, 'start': 0, 'size': 2},
}

def industry_count(name, args, pos, info):
    if len(args) < 1 or len(args) > 2:
        raise generic.ScriptError("'%s'() requires between 1 and 2 argument(s), encountered %d" % (name, len(args)), pos)
    if not isinstance(args[0], expression.ConstantNumeric):
        raise generic.ScriptError("First argument of '%s' must be a compile-time constant." % name, arg.pos)
    generic.check_range(args[0].value, 0, 255, "First argument of '%s'" % name, args[0].pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 1 else args[1]

    var = expression.Variable(expression.ConstantNumeric(info['var']), expression.ConstantNumeric(info['start']), expression.ConstantNumeric((1 << info['size']) - 1), args[0], pos)
    var.extra_params.append( (0x100, grfid) )
    return var

def industry_layout_count(name, args, pos, info):
    if len(args) < 2 or len(args) > 3:
        raise generic.ScriptError("'%s'() requires between 2 and 3 argument(s), encountered %d" % (name, len(args)), pos)
    if not isinstance(args[0], expression.ConstantNumeric):
        raise generic.ScriptError("First argument of '%s' must be a compile-time constant." % name, arg.pos)
    generic.check_range(args[0].value, 0, 255, "First argument of '%s'" % name, args[0].pos)

    grfid = expression.ConstantNumeric(0xFFFFFFFF) if len(args) == 2 else args[2]

    var = expression.Variable(expression.ConstantNumeric(info['var']), expression.ConstantNumeric(info['start']), expression.ConstantNumeric((1 << info['size']) - 1), args[0], pos)
    var.extra_params.append( (0x100, grfid) )
    var.extra_params.append( (0x101, expression.BinOp(nmlop.AND, args[1], expression.ConstantNumeric(0xFF)).reduce()) )
    return var

varact2vars60x_industries = {
    'industry_count': {'var': 0x67, 'start': 16, 'size': 8, 'function': industry_count},
    'industry_distance': {'var': 0x67, 'start': 0, 'size': 16, 'function': industry_count},
    'industry_layout_count': {'var': 0x68, 'start': 16, 'size': 8, 'function': industry_layout_count},
    'industry_layout_distance': {'var': 0x68, 'start': 0, 'size': 16, 'function': industry_layout_count},
}

varact2vars_railtype = {
    'terrain_type' : {'var': 0x40, 'start': 0, 'size': 8},
    'enhanced_tunnels': {'var': 0x41, 'start': 0, 'size': 8},
    'level_crossing_status': {'var': 0x42, 'start': 0, 'size': 8},
    'build_date': {'var': 0x43, 'start': 0, 'size': 32},
}

varact2vars_airporttiles = {
    'terrain_type' : {'var': 0x41, 'start': 0, 'size': 8},
    'town_radius_group': {'var': 0x42, 'start': 0, 'size': 3},
    'relative_pos': {'var': 0x43, 'start': 0, 'size': 24},
    'animation_frame': {'var': 0x44, 'start': 0, 'size': 8},
}

varact2vars[0x00] = varact2vars_trains
varact2vars60x[0x00] = varact2vars60x_vehicles
varact2vars[0x01] = varact2vars_roadvehs
varact2vars60x[0x01] = varact2vars60x_vehicles
varact2vars[0x02] = varact2vars_ships
varact2vars60x[0x02] = varact2vars60x_vehicles
varact2vars[0x03] = varact2vars_aircraft
varact2vars60x[0x03] = varact2vars60x_vehicles
varact2vars[0x09] = varact2vars_industrytiles
varact2vars60x[0x09] = varact2vars60x_industrytiles
varact2vars[0x0A] = varact2vars_industries
varact2vars60x[0x0A] = varact2vars60x_industries
varact2vars[0x10] = varact2vars_railtype
varact2vars[0x11] = varact2vars_airporttiles
