
units = {}

units['nfo'] = {'type': 'nfo', 'convert': 1} #don't convert, take value literal

# Conversion factor works like this:
# 1 reference_unit = convert other_unit
# So nfo_value = property_value / convert * property_specific_conversion_factor

#Speed (reference: m/s)
units['mph'] = {'type': 'speed', 'convert': 2.236936}
units['km/h'] = {'type': 'speed', 'convert': 3.6}
units['m/s'] = {'type': 'speed', 'convert': 1}

#Power (reference: hpI (imperial hp))
units['hp'] = {'type': 'power', 'convert': 1} # Default to imperial hp
units['kW'] = {'type': 'power', 'convert': 0.745699}
units['hpM'] = {'type': 'power', 'convert': 1.013869}
units['hpI'] = {'type': 'power', 'convert': 1}

#Weight (reference: ton)
units['ton'] = {'type': 'weight', 'convert': 1}
units['tons'] = {'type': 'weight', 'convert': 1}
units['kg'] = {'type': 'weight', 'convert': 1000.0}
