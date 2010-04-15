
varact2vars = 12 * [{}]
varact2parent_scope = [0x00, 0x01, 0x02, 0x03, 0x08, None, 0x08, 0x08, None, 0x0A, 0x08, None, None, None, None, None, None]

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
