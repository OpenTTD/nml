
varact2vars = 0x12 * [{}]
# feature number:      0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x08, None, 0x08, 0x08, None, 0x0A, 0x08, None, None, None, None, 0x08, None, None, None]

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
    'extra_callback_info2' : {'var': 0x18, 'start': 0, 'size': 32},
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
    'bitmask_consist_info' : {'var': 0x42, 'start': 24, 'size': 8},
    'company_num' : {'var': 0x43, 'start': 0, 'size': 8},
    'company_type' : {'var': 0x43, 'start': 16, 'size': 2},
    'company_color1' : {'var': 0x43, 'start': 24, 'size': 4},
    'company_color2' : {'var': 0x43, 'start': 28, 'size': 4},
    'aircraft_height' : {'var': 0x44, 'start': 8, 'size': 8},
    'airport_type' : {'var': 0x44, 'start': 0, 'size': 8},
    'curv_info_prev_cur' : {'var': 0x45, 'start': 0, 'size': 4},
    'curv_info_cur_next' : {'var': 0x45, 'start': 8, 'size': 4},
    'curv_info_prev_next' : {'var': 0x45, 'start': 16, 'size': 4},
    'motion_counter' : {'var': 0x46, 'start': 8, 'size': 4},
    'cargo_type_in_veh' : {'var': 0x47, 'start': 0, 'size': 8},
    'cargo_unit_weight' : {'var': 0x47, 'start': 8, 'size': 8},
    'cargo_classes' : {'var': 0x47, 'start': 16, 'size': 16},
    'vehicle_type_info' : {'var': 0x48, 'start': 0, 'size': 2},
    'build_year' : {'var': 0x49, 'start': 0, 'size': 32},
    'vehicle_type_id' : {'var': 0xC6, 'start': 0, 'size': 16},
    'refit_cycle' : {'var': 0xF2, 'start': 0, 'size': 8},
    'vehicle_is_powered' : {'var': 0xFE, 'start': 5, 'size': 1},
    'vehicle_is_not_powered' : {'var': 0xFE, 'start': 6, 'size': 1},
    'vehicle_is_potentially_powered': {'var': 0x4A, 'start': 8, 'size': 1},
    'vehicle_is_reversed' : {'var': 0xFE, 'start': 8, 'size': 1},
    'build_during_preview' : {'var': 0xFE, 'start': 10, 'size': 1},
    'current_railtype': {'var': 0x4A, 'start': 0, 'size': 8},
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

varact2vars[0x00] = veh_vars
varact2vars[0x01] = veh_vars
varact2vars[0x02] = veh_vars
varact2vars[0x03] = veh_vars
varact2vars[0x10] = varact2vars_railtype
varact2vars[0x11] = varact2vars_airporttiles
