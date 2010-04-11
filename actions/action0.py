import ast
from generic import *
from action4 import *
from action6 import *
from actionD import *

class Action0:
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.prop_list = []
        self.num_ids = None
    
    def write(self, file):
        file.write("-1 * 0 00 ")
        print_bytex(file, self.feature)
        print_byte(file, len(self.prop_list))
        if self.num_ids == None: self.num_ids = 1
        print_bytex(file, self.num_ids)
        file.write("FF ")
        print_wordx(file, self.id)
        file.write("\n")
        for prop in self.prop_list:
            prop.write(file)
        file.write("\n")
    
    def skip_action7(self):
        return True
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

first_free_id = 0x12 * [0]

def get_free_id(feature):
    global first_free_id
    first_free_id[feature] += 1
    return first_free_id[feature] - 1

class Action0Property:
    def __init__(self, num, value, size):
        self.num = num
        self.value = value
        self.size = size
        
    def write(self, file):
        print_bytex(file, self.num)
        self.value.write(file, self.size)
        file.write("\n")
    
    def get_size(self):
        return self.size + 1

def train_weight_prop(value):
    if not isinstance(value, ast.ConstantNumeric): raise ScriptError("Train weight must be a constant number")
    low_byte = ast.ConstantNumeric(value.value & 0xFF)
    high_byte = ast.ConstantNumeric(value.value >> 8)
    return [Action0Property(0x16, low_byte, 1), Action0Property(0x24, high_byte, 1)]

properties = 0x12 * [None]

properties[0x00] = {
    'reliability_decay' : {'size': 1, 'num': 0x02},
    'vehicle_life' : {'size': 1, 'num': 0x03},
    'model_life' : {'size': 1, 'num': 0x04},
    'climates_available' : {'size': 1, 'num': 0x06},
    'load_amount' : {'size': 2, 'num': 0x07},
    'track_type' : {'size': 1, 'num': 0x05},
    'ai_special_flag' : {'size': 1, 'num': 0x08},
    'speed' : {'size': 2, 'num': 0x09},
    'power' : {'size': 2, 'num': 0x0B},
    'running_cost_factor' : {'size': 1, 'num': 0x0D},
    'running_cost_base' : {'size': 4, 'num': 0x0E},
    'sprite_id' : {'size': 1, 'num': 0x12},
    'dual_headed' : {'size': 1, 'num': 0x13},
    'cargo_capacity' : {'size': 1, 'num': 0x14},
    'cargo_type' : {'size': 1, 'num': 0x15},
    'weight' : {'custom_function': train_weight_prop},
    'cost_factor' : {'size': 1, 'num': 0x17},
    'ai_engine_rank' : {'size': 1, 'num': 0x18},
    'traction_type' : {'size': 1, 'num': 0x19},
    'weight' : {'size': 1, 'num': 0x1A},
    'extra_power_per_wagon' : {'size': 2, 'num': 0x1B},
    'refit_cost' : {'size': 1, 'num': 0x1C},
    'refittable_cargo_types' : {'size': 4, 'num': 0x1D},
    'callback flags' : {'size': 1, 'num': 0x1E},
    'tractive_effort_coefficient' : {'size': 1, 'num': 0x1F},
    'air_drag_coefficient' : {'size': 1, 'num': 0x20},
    'shorten_vehicle' : {'size': 1, 'num': 0x21},
    'visual_effect' : {'size': 1, 'num': 0x22},
    'extra_weight_per_wagon' : {'size': 1, 'num': 0x23},
    'bitmask_var42' : {'size': 1, 'num': 0x25},
    'retire_early' : {'size': 1, 'num': 0x26},
    'misc_flags' : {'size': 1, 'num': 0x27},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x28},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x29},
    'introduction_date' : {'size': 4, 'num': 0x2A},
}

properties[0x0A] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'layouts': {'size': 0, 'num': 0x0A},
    'prod_flags': {'size': 1, 'num': 0x0B},
    'closure_msg': {'size': 2, 'num': 0x0C},
    'prod_increase_msg': {'size': 2, 'num': 0x0D},
    'prod_decrease_msg': {'size': 2, 'num': 0x0E},
    'fund_cost_multiplier': {'size': 1, 'num': 0x0F},
    'prod_cargo_types': {'size': 2, 'num': 0x10},
    'accept_cargo_types': {'size': 4, 'num': 0x11},
    'prod_multiplier_1': {'size': 1, 'num': 0x12},
    'prod_multiplier_2': {'size': 1, 'num': 0x13},
    'min_cargo_distr': {'size': 1, 'num': 0x14},
    'random_sound_effects': {'size': 0, 'num': 0x15},
    'conflicting_ind_types': {'size': 0, 'num': 0x16},
    'prob_random': {'size': 1, 'num': 0x17},
    'prob_in_game': {'size': 1, 'num': 0x18},
    'map_color': {'size': 1, 'num': 0x19},
    'spec_flags': {'size': 4, 'num': 0x1A},
    'new_ind_text': {'size': 2, 'num': 0x1B},
    'input_multiplier_1': {'size': 4, 'num': 0x1C},
    'input_multiplier_2': {'size': 4, 'num': 0x1D},
    'input_multiplier_3': {'size': 4, 'num': 0x1E},
    'ind_name': {'size': 2, 'num': 0x1F, 'string': 0xDC},
    'prospect_chance': {'size': 4, 'num': 0x20},
    'callback_flags_1': {'size': 1, 'num': 0x21},
    'callback_flags_2': {'size': 1, 'num': 0x22},
    'remove_cost_multiplier': {'size': 4, 'num': 0x23},
    'nearby_station_name': {'size': 2, 'num': 0x24},
}


def parse_property(feature, name, value):
    global properties
    prop = None
    action_list = []
    action_list_append = []
    mods = []
    
    if isinstance(name, str):
        if not name in properties[feature]: raise ScriptError("Unkown property name: " + name)
        prop = properties[feature][name]
    elif isinstance(name, ast.ConstantNumeric):
        for p in properties[feature]:
            if 'num' in p and p['num'] != name.value: continue
            prop = p
        if prop == None: raise ScriptError("Unkown property number: " + name.value)
    else: raise ScriptError("Invalid type as property identifier")
    
    if 'custom_function' in prop:
        props = prop['custom_function'](value)
    else:
        if isinstance(value, ast.ConstantNumeric):
            pass
        elif isinstance(value, ast.Parameter) and isinstance(value.num, ast.ConstantNumeric):
            mods.append((value.num.value, size, 1))
            value = ast.ConstantNumeric(0)
        elif isinstance(value, ast.String):
            if not 'string' in prop: raise ScriptError("String used as value for non-string property: " + str(prop['num']))
            string_range = prop['string']
            stringid, prepend, string_actions = get_string_action4s(feature, string_range, value)
            value = ast.ConstantNumeric(stringid)
            if prepend:
                action_list.extend(string_actions)
            else:
                action_list_append.extend(string_actions)
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(value)
            mods.append((tmp_param, size, 1))
            action_list.extend(tmp_param_actions)
            value = ast.ConstantNumeric(0)
        props = [Action0Property(prop['num'], value, prop['size'])]
    
    return (props, action_list, mods, action_list_append)

def parse_property_block(prop_list, feature, id):
    global free_parameters
    free_parameters_backup = free_parameters[:]
    action_list = []
    action_list_append = []
    action6 = Action6()
    if isinstance(id, ast.ConstantNumeric):
        action0 = Action0(feature, id.value)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(id)
        action6.modify_bytes(tmp_param, 2, 5)
        action_list.extend(tmp_param_actions)
        action0 = Action0(feature, 0)
    
    offset = 7
    for prop in prop_list:
        properties, extra_actions, mods, extra_append_actions = parse_property(feature, prop.name, prop.value)
        action_list.extend(extra_actions)
        action_list_append.extend(extra_append_actions)
        for mod in mods:
            action6.modify_bytes(mod[0], mod[1], mod[2] + offset)
        for p in properties:
            offset += p.get_size()
        action0.prop_list.extend(properties)
    
    if len(action6.modifications) > 0: action_list.append(action6)
    action_list.append(action0)
    action_list.extend(action_list_append)
    
    free_parameters = free_parameters_backup
    return action_list

class CargoListProp:
    def __init__(self, cargo_list):
        self.cargo_list = cargo_list
    
    def write(self, file):
        print_bytex(file, 0x09)
        for i in range(0, len(self.cargo_list)):
            print_string(file, self.cargo_list[i], False, True)
            if i > 0 and i % 5 == 0: file.write("\n")

def get_cargolist_action(cargo_list):
    action0 = Action0(0x08, 0)
    action0.prop_list.append(CargoListProp(cargo_list))
    action0.num_ids = len(cargo_list)
    return [action0]