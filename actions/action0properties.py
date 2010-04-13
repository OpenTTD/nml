import ast
from action0 import *

properties = 0x12 * [None]

def train_weight_prop(value):
    if not isinstance(value, ast.ConstantNumeric): raise ScriptError("Train weight must be a constant number")
    low_byte = ast.ConstantNumeric(value.value & 0xFF)
    high_byte = ast.ConstantNumeric(value.value >> 8)
    return [Action0Property(0x16, low_byte, 1), Action0Property(0x24, high_byte, 1)]

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