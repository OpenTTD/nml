callbacks = 0x12 * [{}]

# Possible values for 'purchase':
# 0 (or not set): not called from purchase list
# 1: called normally and from purchase list
# 2: only called from purchase list
# 'cbname': as 1) but if 'cbname' is set also, then 'cbname' overrides this
# in the purchase list. 'cbname' should have a value of 2 for 'purchase'


# Callbacks common to all vehicle types
general_vehicle_cbs = {
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
