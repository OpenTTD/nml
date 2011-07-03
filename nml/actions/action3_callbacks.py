callbacks = 0x12 * [{}]

# Possible values for 'purchase':
# 0 (or not set): not called from purchase list
# 1: called normally and from purchase list
# 2: only called from purchase list
# 'cbname': as 1) but if 'cbname' is set also, then 'cbname' overrides this
# in the purchase list. 'cbname' should have a value of 2 for 'purchase'


# Callbacks common to all vehicle types
general_vehicle_cbs = {
    'default' : {'cargo': None},
    'purchase' : {'cargo': 0xFF},
    'random_trigger' : {'num': 0x01}, # Almost undocumented, but really neccesary!
    'loading_speed' : {'num': 0x12, 'flag_bit': 2},
    'cargo_subtype' : {'num': 0x19, 'flag_bit': 5},
    'additional_text' : {'num': 0x23, 'purchase': 2},
    'colour_mapping' : {'num': 0x2D, 'flag_bit':6, 'purchase': 'purchase_colour_mapping'},
    'purchase_colour_mapping' : {'num': 0x2D, 'flag_bit':6, 'purchase': 2},
    'start_stop' : {'num': 0x31},
    'every_32_days' : {'num': 0x32},
    'sound_effect' : {'num': 0x33, 'flag_bit': 7},
}

# Trains
callbacks[0x00] = {
    'visual_effect_and_powered' : {'num': 0x10, 'flag_bit': 0},
    'shorten_vehicle' : {'num': 0x11, 'flag_bit': 1}, # Should this become 'length' at some point (with inverted meaning)? 
    'cargo_capacity' : [{'num': 0x15, 'flag_bit': 3}, {'num': 0x36, 'var10': 0x14, 'purchase': 'purchase_cargo_capacity'}],
    'purchase_cargo_capacity' : {'num': 0x36, 'var10': 0x14, 'purchase': 2},
    'articulated_part' : {'num': 0x16, 'flag_bit': 4, 'purchase': 1}, # Don't add separate purchase CB here
    'can_attach_wagon' : {'num': 0x1D},
    'speed' : {'num': 0x36, 'var10': 0x09, 'purchase': 'purchase_speed'},
    'purchase_speed' : {'num': 0x36, 'var10': 0x09, 'purchase': 2},
    'power' : {'num': 0x36, 'var10': 0x0B, 'purchase': 'purchase_power'},
    'purchase_power' : {'num': 0x36, 'var10': 0x0B, 'purchase': 2},
    'running_cost_factor' : {'num': 0x0D, 'var10': 0x14, 'purchase': 'purchase_running_cost_factor'},
    'purchase_running_cost_factor' : {'num': 0x0D, 'var10': 0x14, 'purchase': 2},
    'weight' : {'num': 0x36, 'var10': 0x16, 'purchase': 'purchase_weight'},
    'purchase_weight' : {'num': 0x36, 'var10': 0x16, 'purchase': 2},
    'cost_factor' : {'num': 0x36, 'var10': 0x17, 'purchase': 2},
    'tractive_effort_coefficient' : {'num': 0x36, 'var10': 0x1F, 'purchase': 'purchase_tractive_effort_coefficient'},
    'purchase_tractive_effort_coefficient' : {'num': 0x36, 'var10': 0x1F, 'purchase': 2},
    'bitmask_vehicle_info' : {'num': 0x36, 'var10': 0x25},
}
callbacks[0x00].update(general_vehicle_cbs)

# Road vehicles
callbacks[0x01] = {
    'visual_effect' : {'num': 0x10, 'flag_bit': 0},
    'shorten_vehicle' : {'num': 0x11, 'flag_bit': 1}, # Should this become 'length' at some point (with inverted meaning)? 
    'cargo_capacity' : [{'num': 0x15, 'flag_bit': 3}, {'num': 0x36, 'var10': 0x0F, 'purchase': 'purchase_cargo_capacity'}],
    'purchase_cargo_capacity' : {'num': 0x36, 'var10': 0x0F, 'purchase': 2},
    'articulated_part' : {'num': 0x16, 'flag_bit': 4,  'purchase': 1}, # Don't add separate purchase CB here
    'running_cost_factor' : {'num': 0x36, 'var10': 0x09, 'purchase': 'purchase_running_cost_factor'},
    'purchase_running_cost_factor' : {'num': 0x36, 'var10': 0x09, 'purchase': 2},
    'cost_factor' : {'num': 0x36, 'var10': 0x11, 'purchase': 2},
    'power' : {'num': 0x36, 'var10': 0x13, 'purchase': 'purchase_power'},
    'purchase_power' : {'num': 0x36, 'var10': 0x13, 'purchase': 2},
    'weight' : {'num': 0x36, 'var10': 0x14, 'purchase': 'purchase_weight'},
    'purchase_weight' : {'num': 0x36, 'var10': 0x14, 'purchase': 2},
    'speed' : {'num': 0x36, 'var10': 0x15, 'purchase': 'purchase_speed'},
    'purchase_speed' : {'num': 0x36, 'var10': 0x15, 'purchase': 2},
    'tractive_effort_coefficient' : {'num': 0x36, 'var10': 0x18, 'purchase': 'purchase_tractive_effort_coefficient'},
    'purchase_tractive_effort_coefficient' : {'num': 0x36, 'var10': 0x18, 'purchase': 2},
    
}
callbacks[0x01].update(general_vehicle_cbs)

# Ships
callbacks[0x02] = {
    'visual_effect' : {'num': 0x10, 'flag_bit': 0},
    'cargo_capacity' : [{'num': 0x15, 'flag_bit': 3}, {'num': 0x36, 'var10': 0x0D, 'purchase': 'purchase_cargo_capacity'}],
    'purchase_cargo_capacity' : {'num': 0x36, 'var10': 0x0D, 'purchase': 2},
    'cost_factor' : {'num': 0x36, 'var10': 0x0A, 'purchase': 2},
    'speed' : {'num': 0x36, 'var10': 0x0B, 'purchase': 'purchase_speed'},
    'purchase_speed' : {'num': 0x36, 'var10': 0x0B, 'purchase': 2},
    'running_cost_factor' : {'num': 0x36, 'var10': 0x0F, 'purchase': 'purchase_running_cost_factor'},
    'purchase_running_cost_factor' : {'num': 0x36, 'var10': 0x0F, 'purchase': 2},
}
callbacks[0x02].update(general_vehicle_cbs)

# Aircraft
callbacks[0x03] = {
    'passenger_capacity' : [{'num': 0x15, 'flag_bit': 3}, {'num': 0x36, 'var10': 0x0F, 'purchase': 'purchase_passenger_capacity'}],
    'purchase_passenger_capacity' : {'num': 0x36, 'var10': 0x0F, 'purchase': 2},
    'cost_factor' : {'num': 0x36, 'var10': 0x0B, 'purchase': 2},
    'speed' : {'num': 0x36, 'var10': 0x0C, 'purchase': 'purchase_speed'},
    'purchase_speed' : {'num': 0x36, 'var10': 0x0C, 'purchase': 2},
    'running_cost_factor' : {'num': 0x36, 'var10': 0x0E, 'purchase': 'purchase_running_cost_factor'},
    'purchase_running_cost_factor' : {'num': 0x36, 'var10': 0x0E, 'purchase': 2},
    'mail_capacity' : {'num': 0x36, 'var10': 0x11, 'purchase': 'purchase_mail_capacity'},
    'purchase_mail_capacity' : {'num': 0x36, 'var10': 0x11, 'purchase': 2},
}
callbacks[0x03].update(general_vehicle_cbs)

# Stations (0x04) are not yet implemented

# Canals (missing callbacks)
callbacks[0x05] = {
    'default' : {'cargo': None},
}

# Bridges (0x06) have no action3

# Houses (incomplete)
callbacks[0x07] = {
    'default' : {'cargo': None},
}

# General variables (0x08) have no action3

# Industry tiles
callbacks[0x09] = {
    'anim_control'        : {'num': 0x25},
    'anim_next_frame'     : {'num': 0x26, 'flag_bit': 0},
    'anim_speed'          : {'num': 0x27, 'flag_bit': 1},
    'cargo_amount_accept' : {'num': 0x2B, 'flag_bit': 2},
    'cargo_type_accept'   : {'num': 0x2C, 'flag_bit': 3},
    'slope_is_suitable'   : {'num': 0x2F, 'flag_bit': 4},
    'foundations'         : {'num': 0x30, 'flag_bit': 5},
    'autoslope'           : {'num': 0x3B, 'flag_bit': 6},
    'default'             : {'cargo': None},
}

# Industries
callbacks[0x0A] = {
    'availability'          : {'num': 0x22,  'flag_bit': 0},
    'produce_cargo_arrival' : {'num': 0x00,  'flag_bit': 1, 'var18': 0},
    'produce_256_ticks'     : {'num': 0x00,  'flag_bit': 2, 'var18': 1},
    'location_check'        : {'num': 0x28,  'flag_bit': 3},
    'random_prod_change'    : {'num': 0x29,  'flag_bit': 4},
    'monthly_prod_change'   : {'num': 0x35,  'flag_bit': 5},
    'cargo_subtype_display' : {'num': 0x37,  'flag_bit': 6},
    'extra_text_fund'       : {'num': 0x38,  'flag_bit': 7},
    'extra_text_industry'   : {'num': 0x3A,  'flag_bit': 8},
    'control_special'       : {'num': 0x3B,  'flag_bit': 9},
    'stop_accept_cargo'     : {'num': 0x3D,  'flag_bit': 10},
    'colour'                : {'num': 0x14A, 'flag_bit': 11},
    'cargo_input'           : {'num': 0x14B, 'flag_bit': 12},
    'cargo_output'          : {'num': 0x14C, 'flag_bit': 13},
    'default'               : {'cargo': None},
}

# Cargos (incomplete)
callbacks[0x0B] = {
    'default' : {'cargo': None},
}

# Sound effects (0x0C) have no item-specific action3

# Airports (incomplete)
callbacks[0x0D] = {
    'default' : {'cargo': None},
}

# New signals (0x0E) have no item-specific action3

# Objects
callbacks[0x0F] = {
    'slope_check'     : {'num': 0x157, 'flag_bit': 0, 'purchase': 2},
    'anim_next_frame' : {'num': 0x158, 'flag_bit': 1},
    'anim_control'    : {'num': 0x159},
    'anim_speed'      : {'num': 0x15A, 'flag_bit': 2},
    'colour'          : {'num': 0x15B, 'flag_bit': 3},
    'additional_text' : {'num': 0x15C, 'flag_bit': 4, 'purchase': 2},
    'autoslope'       : {'num': 0x15D, 'flag_bit': 5},
    'default'         : {'cargo': None},
    'purchase'        : {'cargo': 0xFF},
}

# Railtypes
callbacks[0x10] = {
    # No default here, it makse no sense
    'gui'             : {'cargo': 0x00},
    'track_overlay'   : {'cargo': 0x01},
    'underlay'        : {'cargo': 0x02},
    'tunnels'         : {'cargo': 0x03},
    'catenary_wire'   : {'cargo': 0x04},
    'catenary_pylons' : {'cargo': 0x05},
    'bridge_surfaces' : {'cargo': 0x06},
    'level_crossings' : {'cargo': 0x07},
    'depots'          : {'cargo': 0x08},
    'fences'          : {'cargo': 0x09},
}

# Airport tiles (incomplete)
callbacks[0x11] = {
    'default' : {'cargo': None},
}
