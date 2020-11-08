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

from nml import global_constants, tokens, unit
from nml.actions import (
    action0properties,
    action2layout,
    action2var_variables,
    action3_callbacks,
    action5,
    action12,
    actionB,
    real_sprite,
)
from nml.ast import basecost, general, switch
from nml.expression import functioncall

# Create list of blocks, functions and units
units = set(unit.units.keys())
keywords = set(tokens.reserved.keys())
functions = set(functioncall.function_table.keys())
layouts = set(action2layout.layout_sprite_types.keys())

# No easy way to get action14 stuff
temp1 = units | keywords | functions | layouts | {"int", "bool"}
block_names_table = sorted(temp1)


# Create list of properties and variables
var_tables = [
    action2var_variables.varact2_globalvars,
    action2var_variables.varact2vars_vehicles,
    action2var_variables.varact2vars_trains,
    action2var_variables.varact2vars_roadvehs,
    action2var_variables.varact2vars_ships,
    action2var_variables.varact2vars_aircraft,
    action2var_variables.varact2vars60x_vehicles,
    action2var_variables.varact2vars_base_stations,
    action2var_variables.varact2vars60x_base_stations,
    action2var_variables.varact2vars_stations,
    action2var_variables.varact2vars60x_stations,
    action2var_variables.varact2vars_canals,
    action2var_variables.varact2vars_houses,
    action2var_variables.varact2vars60x_houses,
    action2var_variables.varact2vars_industrytiles,
    action2var_variables.varact2vars60x_industrytiles,
    action2var_variables.varact2vars_industries,
    action2var_variables.varact2vars60x_industries,
    action2var_variables.varact2vars_airports,
    action2var_variables.varact2vars_objects,
    action2var_variables.varact2vars60x_objects,
    action2var_variables.varact2vars_railtype,
    action2var_variables.varact2vars_roadtype,
    action2var_variables.varact2vars_tramtype,
    action2var_variables.varact2vars_airporttiles,
    action2var_variables.varact2vars60x_airporttiles,
    action2var_variables.varact2vars_towns,
]

variables = set()
for d in var_tables:
    for key in d.keys():
        variables.add(key)

prop_tables = [
    action0properties.general_veh_props,
    action0properties.properties[0x00],
    action0properties.properties[0x01],
    action0properties.properties[0x02],
    action0properties.properties[0x03],
    action0properties.properties[0x05],
    action0properties.properties[0x07],
    action0properties.properties[0x09],
    action0properties.properties[0x0A],
    action0properties.properties[0x0B],
    action0properties.properties[0x0D],
    action0properties.properties[0x0F],
    action0properties.properties[0x10],
    action0properties.properties[0x11],
    action0properties.properties[0x12],
    action0properties.properties[0x13],
]

properties = set()
for d in prop_tables:
    for key in d.keys():
        properties.add(key)

dummy = action2layout.Action2LayoutSprite(None, None)
layout_sprites = set(dummy.params.keys())

cb_tables = [
    action3_callbacks.general_vehicle_cbs,
    action3_callbacks.callbacks[0x00],
    action3_callbacks.callbacks[0x01],
    action3_callbacks.callbacks[0x02],
    action3_callbacks.callbacks[0x03],
    action3_callbacks.callbacks[0x04],
    action3_callbacks.callbacks[0x05],
    action3_callbacks.callbacks[0x07],
    action3_callbacks.callbacks[0x09],
    action3_callbacks.callbacks[0x0A],
    action3_callbacks.callbacks[0x0B],
    action3_callbacks.callbacks[0x0D],
    action3_callbacks.callbacks[0x0F],
    action3_callbacks.callbacks[0x10],
    action3_callbacks.callbacks[0x11],
    action3_callbacks.callbacks[0x12],
    action3_callbacks.callbacks[0x13],
]

callbacks = set()
for d in cb_tables:
    for key in d.keys():
        callbacks.add(key)

# No easy way to get action14 stuff
act14_vars = {
    "grfid",
    "name",
    "desc",
    "version",
    "min_compatible_version",
    "type",
    "bit",
    "min_value",
    "max_value",
    "def_value",
    "names",
}

temp2 = variables | properties | layout_sprites | callbacks | act14_vars
variables_names_table = sorted(temp2)

# Create list of features
features = set(general.feature_ids.keys())
switch_names = set(switch.var_ranges.keys())

temp3 = features | switch_names
feature_names_table = sorted(temp3)

# Create list of callbacks constants
const_tables = [
    global_constants.constant_numbers,
    global_constants.global_parameters,
    global_constants.misc_grf_bits,
    global_constants.patch_variables,
    global_constants.config_flags,
    global_constants.unified_maglev_var,
    global_constants.railtype_table,
    global_constants.roadtype_table,
    global_constants.tramtype_table,
]

constant_names = set()
for d in const_tables:
    for key in d.keys():
        constant_names.add(key)

act5_names = set(action5.action5_table.keys())
act12_names = set(action12.font_sizes.keys())
actB_names = set(actionB.default_error_msg.keys()) | set(actionB.error_severity.keys())
sprite_names = set(real_sprite.real_sprite_flags.keys())
cost_names = set(basecost.base_cost_table.keys()) | set(basecost.generic_base_costs)

temp4 = constant_names | act5_names | act12_names | actB_names | sprite_names | cost_names
callback_names_table = sorted(temp4)
