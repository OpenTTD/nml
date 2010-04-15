
varact2vars = 12 * [{}]
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x08, None, 0x08, 0x08, None, 0x0A, 0x08, None, None, None, None, None, None]

varact2_globalvars = {
    'days_since_1920' : {'var': 0x00, 'start': 0, 'size': 16},
    'years_since_1920' : {'var': 0x01, 'start': 0, 'size': 8},
    'current_month' : {'var': 0x02, 'start': 0, 'size': 8},
    'current_day_of_month' : {'var': 0x02, 'start': 8, 'size': 5},
    'is_leapyear' : {'var': 0x02, 'start': 15, 'size': 1},
    'current_day_of_year' : {'var': 0x02, 'start': 16, 'size': 9},
    'current_climate' : {'var': 0x03, 'start': 0, 'size': 2},
    'date_fraction' : {'var': 0x09, 'start': 0, 'size': 16},
    'animation_counter' : {'var': 0x0A, 'start': 0, 'size': 16},
    'current_callback' : {'var': 0x0C, 'start': 0, 'size': 16},
    'extra_callback_info1' : {'var': 0x10, 'start': 0, 'size': 32},
    'game_mode' : {'var': 0x12, 'start': 0, 'size': 2},
    'extra_callback_info1' : {'var': 0x18, 'start': 0, 'size': 32},
    'display_options' : {'var': 0x1B, 'start': 0, 'size': 6},
    'last_varact2_result' : {'var': 0x1C, 'start': 0, 'size': 32},
    'snowline_height' : {'var': 0x20, 'start': 0, 'size': 8},
    'days_since_0' : {'var': 0x23, 'start': 0, 'size': 32},
    'years_since_0' : {'var': 0x24, 'start': 0, 'size': 32},
}

veh_vars = {
    'position_in_consist' : {'var': 0x40, 'start': 0, 'size': 8},
    'position_in_consist_from_end' : {'var': 0x40, 'start': 8, 'size': 8},
    'num_vehs_in_consist' : {'var': 0x40, 'start': 16, 'size': 8},
    'position_in_vehid_chain' : {'var': 0x41, 'start': 0, 'size': 8},
    'position_in_vehid_chain_from_end' : {'var': 0x41, 'start': 8, 'size': 8},
    'num_vehs_in_vehid_chain' : {'var': 0x41, 'start': 16, 'size': 8},
    'cargo_classes_in_consist' : {'var': 0x42, 'start': 0, 'size': 8},
    'most_common_refit' : {'var': 0x42, 'start': 16, 'size': 8},
    'or_of_bitmask' : {'var': 0x42, 'start': 24, 'size': 8},
    'company_num' : {'var': 0x43, 'start': 0, 'size': 8},
    'company_type' : {'var': 0x43, 'start': 16, 'size': 8},
    'company_color1' : {'var': 0x43, 'start': 24, 'size': 4},
    'company_color2' : {'var': 0x43, 'start': 28, 'size': 4},
}

varact2vars[0x00] = veh_vars
varact2vars[0x01] = veh_vars
varact2vars[0x02] = veh_vars
varact2vars[0x03] = veh_vars
