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

from nml import expression, generic, nmlop


def constant_number(name, info, pos):
    if isinstance(info, str):
        generic.print_warning(
            generic.Warning.DEPRECATION, "'{}' is deprecated, consider using '{}' instead".format(name, info), pos
        )
        info = constant_numbers[info]
    return expression.ConstantNumeric(info, pos)


# fmt: off
constant_numbers = {
    # climates
    "CLIMATE_TEMPERATE"     : 0,
    "CLIMATE_ARCTIC"        : 1,
    "CLIMATE_TROPIC"        : 2,
    "CLIMATE_TROPICAL"      : 2,
    "CLIMATE_TOYLAND"       : 3,
    "ABOVE_SNOWLINE"        : 11,  # Only for house property available_mask

    "NO_CLIMATE"            : 0x00,
    "ALL_CLIMATES"          : 0x0F,

    # never expire
    "VEHICLE_NEVER_EXPIRES" : 0xFF,

    # default_cargo
    "DEFAULT_CARGO_FIRST_REFITTABLE" : 0xFF,

    # cargo classes
    "CC_PASSENGERS"   : 0,
    "CC_MAIL"         : 1,
    "CC_EXPRESS"      : 2,
    "CC_ARMOURED"     : 3,
    "CC_BULK"         : 4,
    "CC_PIECE_GOODS"  : 5,
    "CC_LIQUID"       : 6,
    "CC_REFRIGERATED" : 7,
    "CC_HAZARDOUS"    : 8,
    "CC_COVERED"      : 9,
    "CC_OVERSIZED"    : 10,
    "CC_POWDERIZED"   : 11,
    "CC_NON_POURABLE" : 12,
    "CC_NEO_BULK"     : 12,
    "CC_SPECIAL"      : 15,
    "NO_CARGO_CLASS"           : 0,
    "ALL_NORMAL_CARGO_CLASSES" : 0x1FFF,
    "ALL_CARGO_CLASSES"        : 0x9FFF,

    # engine class
    "ENGINE_CLASS_STEAM"    : 0x00,
    "ENGINE_CLASS_DIESEL"   : 0x08,
    "ENGINE_CLASS_ELECTRIC" : 0x28,
    "ENGINE_CLASS_MONORAIL" : 0x32,
    "ENGINE_CLASS_MAGLEV"   : 0x38,

    # running costs
    "RUNNING_COST_STEAM"    : 0x4C30,
    "RUNNING_COST_DIESEL"   : 0x4C36,
    "RUNNING_COST_ELECTRIC" : 0x4C3C,
    "RUNNING_COST_ROADVEH"  : 0x4C48,
    "RUNNING_COST_NONE"     : 0x0000,

    # shorten factor
    "SHORTEN_TO_8_8" : 0x00,
    "SHORTEN_TO_7_8" : 0x01,
    "SHORTEN_TO_6_8" : 0x02,
    "SHORTEN_TO_5_8" : 0x03,
    "SHORTEN_TO_4_8" : 0x04,
    "SHORTEN_TO_3_8" : 0x05,
    "SHORTEN_TO_2_8" : 0x06,
    "SHORTEN_TO_1_8" : 0x07,

    # vehicle length
    "VEHICLE_LENGTH" : 8,

    # visual effect
    "VISUAL_EFFECT_DEFAULT"  : 0x00,
    "VISUAL_EFFECT_STEAM"    : 0x10,
    "VISUAL_EFFECT_DIESEL"   : 0x20,
    "VISUAL_EFFECT_ELECTRIC" : 0x30,
    "VISUAL_EFFECT_DISABLE"  : 0x40,

    # effect spawn model
    "EFFECT_SPAWN_MODEL_NONE"    : 0x40,
    "EFFECT_SPAWN_MODEL_STEAM"   : 0x41,
    "EFFECT_SPAWN_MODEL_DIESEL"  : 0x42,
    "EFFECT_SPAWN_MODEL_ELECTRIC": 0x43,

    # visual effect / effect spawn model
    "ENABLE_WAGON_POWER"     : 0x00,
    "DISABLE_WAGON_POWER"    : 0x80,

    # create_effect
    "EFFECT_SPRITE_STEAM"                    : 0xF1,
    "EFFECT_SPRITE_DIESEL"                   : 0xF2,
    "EFFECT_SPRITE_ELECTRIC"                 : 0xF3,
    "EFFECT_SPRITE_AIRCRAFT_BREAKDOWN_SMOKE" : 0xFA,
    "EFFECT_SPRITE_NONE"                     : 0xFF,

    "CB_RESULT_CREATE_EFFECT_CENTER"         : 0x2000,
    "CB_RESULT_CREATE_EFFECT_NO_ROTATION"    : 0x4000,

    # train misc flags
    "TRAIN_FLAG_TILT" : 0,
    "TRAIN_FLAG_2CC"  : 1,
    "TRAIN_FLAG_MU"   : 2,
    "TRAIN_FLAG_FLIP" : 3,
    "TRAIN_FLAG_AUTOREFIT": 4,
    "TRAIN_FLAG_NO_BREAKDOWN_SMOKE": 6,
    "TRAIN_FLAG_SPRITE_STACK": 7,

    # roadveh misc flags
    "ROADVEH_FLAG_TRAM" : 0,
    "ROADVEH_FLAG_2CC"  : 1,
    "ROADVEH_FLAG_AUTOREFIT": 4,
    "ROADVEH_FLAG_NO_BREAKDOWN_SMOKE": 6,
    "ROADVEH_FLAG_SPRITE_STACK": 7,

    # ship misc flags
    "SHIP_FLAG_2CC"  : 1,
    "SHIP_FLAG_AUTOREFIT": 4,
    "SHIP_FLAG_NO_BREAKDOWN_SMOKE": 6,
    "SHIP_FLAG_SPRITE_STACK": 7,

    # aircrafts misc flags
    "AIRCRAFT_FLAG_2CC"  : 1,
    "AIRCRAFT_FLAG_AUTOREFIT": 4,
    "AIRCRAFT_FLAG_NO_BREAKDOWN_SMOKE": 6,
    "AIRCRAFT_FLAG_SPRITE_STACK": 7,

    # for those, who can't tell the difference between a train and an aircraft:
    "VEHICLE_FLAG_2CC" : 1,
    "VEHICLE_FLAG_AUTOREFIT": 4,
    "VEHICLE_FLAG_NO_BREAKDOWN_SMOKE": 6,

    # Graphic flags for waterfeatures
    "WATERFEATURE_ALTERNATIVE_SPRITES" : 0,

    # IDs for waterfeatures
    "WF_WATERCLIFFS" : 0x00,
    "WF_LOCKS"       : 0x01,
    "WF_DIKES"       : 0x02,
    "WF_CANAL_GUI"   : 0x03,
    "WF_FLAT_DOCKS"  : 0x04,
    "WF_RIVER_SLOPE" : 0x05,
    "WF_RIVERBANKS"  : 0x06,
    "WF_RIVER_GUI"   : 0x07,
    "WF_BUOY"        : 0x08,

    # ai flags
    "AI_FLAG_PASSENGER" : 0x01,
    "AI_FLAG_CARGO"     : 0x00,

    # Callback results
    "CB_RESULT_ATTACH_ALLOW_IF_RAILTYPES"  : 0x400,
    "CB_RESULT_ATTACH_ALLOW"               : 0x401,
    "CB_RESULT_ATTACH_DISALLOW"            : 0x402,

    "CB_RESULT_NO_MORE_ARTICULATED_PARTS"  : 0x7FFF,
    "CB_RESULT_REVERSED_VEHICLE"           : 0x4000,

    "CB_RESULT_32_DAYS_TRIGGER"            : 0,
    "CB_RESULT_32_DAYS_COLOUR_MAPPING"     : 1,

    "CB_RESULT_COLOUR_MAPPING_ADD_CC"      : 0x4000,

    "CB_RESULT_AUTOREFIT"                  : 0x4000,
    "CB_RESULT_REFIT_COST_MASK"            : 0x3FFF,

    "CB_RESULT_NO_SOUND"                   : 0x7EFF,  # Never a valid sound id

    # Callback results in registers
    "CB_FLAG_MORE_SPRITES"                 : 0x80000000,

    # 1-based, not 0-based
    "SOUND_EVENT_START"                    : 1,
    "SOUND_EVENT_TUNNEL"                   : 2,
    "SOUND_EVENT_BREAKDOWN"                : 3,
    "SOUND_EVENT_RUNNING"                  : 4,
    "SOUND_EVENT_TOUCHDOWN"                : 5,
    "SOUND_EVENT_VISUAL_EFFECT"            : 6,
    "SOUND_EVENT_RUNNING_16"               : 7,
    "SOUND_EVENT_STOPPED"                  : 8,
    "SOUND_EVENT_LOAD_UNLOAD"              : 9,

    # sound effects
    "SOUND_SPLAT"                          : 0x00,
    "SOUND_FACTORY_WHISTLE"                : 0x01,
    "SOUND_TRAIN"                          : 0x02,
    "SOUND_TRAIN_THROUGH_TUNNEL"           : 0x03,
    "SOUND_SHIP_HORN"                      : 0x04,
    "SOUND_FERRY_HORN"                     : 0x05,
    "SOUND_PLANE_TAKE_OFF"                 : 0x06,
    "SOUND_JET"                            : 0x07,
    "SOUND_TRAIN_HORN"                     : 0x08,
    "SOUND_MINING_MACHINERY"               : 0x09,
    "SOUND_ELECTRIC_SPARK"                 : 0x0A,
    "SOUND_STEAM"                          : 0x0B,
    "SOUND_LEVEL_CROSSING"                 : 0x0C,
    "SOUND_VEHICLE_BREAKDOWN"              : 0x0D,
    "SOUND_TRAIN_BREAKDOWN"                : 0x0E,
    "SOUND_CRASH"                          : 0x0F,
    "SOUND_EXPLOSION"                      : 0x10,
    "SOUND_BIG_CRASH"                      : 0x11,
    "SOUND_CASHTILL"                       : 0x12,
    "SOUND_BEEP"                           : 0x13,
    "SOUND_MORSE"                          : 0x14,
    "SOUND_SKID_PLANE"                     : 0x15,
    "SOUND_HELICOPTER"                     : 0x16,
    "SOUND_BUS_START_PULL_AWAY"            : 0x17,
    "SOUND_BUS_START_PULL_AWAY_WITH_HORN"  : 0x18,
    "SOUND_TRUCK_START"                    : 0x19,
    "SOUND_TRUCK_START_2"                  : 0x1A,
    "SOUND_APPLAUSE"                       : 0x1B,
    "SOUND_OOOOH"                          : 0x1C,
    "SOUND_SPLAT_2"                        : 0x1D,
    "SOUND_SPLAT_3"                        : 0x1E,
    "SOUND_JACKHAMMER"                     : 0x1F,
    "SOUND_CAR_HORN"                       : 0x20,
    "SOUND_CAR_HORN_2"                     : 0x21,
    "SOUND_SHEEP"                          : 0x22,
    "SOUND_COW"                            : 0x23,
    "SOUND_HORSE"                          : 0x24,
    "SOUND_BLACKSMITH_ANVIL"               : 0x25,
    "SOUND_SAWMILL"                        : 0x26,
    "SOUND_GOOD_YEAR"                      : 0x27,
    "SOUND_BAD_YEAR"                       : 0x28,
    "SOUND_RIP"                            : 0x29,
    "SOUND_EXTRACT_AND_POP"                : 0x2A,
    "SOUND_COMEDY_HIT"                     : 0x2B,
    "SOUND_MACHINERY"                      : 0x2C,
    "SOUND_RIP_2"                          : 0x2D,
    "SOUND_EXTRACT_AND_POP_2"              : 0x2E,
    "SOUND_POP"                            : 0x2F,
    "SOUND_CARTOON_SOUND"                  : 0x30,
    "SOUND_EXTRACT"                        : 0x31,
    "SOUND_POP_2"                          : 0x32,
    "SOUND_PLASTIC_MINE"                   : 0x33,
    "SOUND_WIND"                           : 0x34,
    "SOUND_COMEDY_BREAKDOWN"               : 0x35,
    "SOUND_CARTOON_CRASH"                  : 0x36,
    "SOUND_BALLOON_SQUEAK"                 : 0x37,
    "SOUND_CHAINSAW"                       : 0x38,
    "SOUND_HEAVY_WIND"                     : 0x39,
    "SOUND_COMEDY_BREAKDOWN_2"             : 0x3A,
    "SOUND_JET_OVERHEAD"                   : 0x3B,
    "SOUND_COMEDY_CAR"                     : 0x3C,
    "SOUND_ANOTHER_JET_OVERHEAD"           : 0x3D,
    "SOUND_COMEDY_CAR_2"                   : 0x3E,
    "SOUND_COMEDY_CAR_3"                   : 0x3F,
    "SOUND_COMEDY_CAR_START_AND_PULL_AWAY" : 0x40,
    "SOUND_MAGLEV"                         : 0x41,
    "SOUND_LOON_BIRD"                      : 0x42,
    "SOUND_LION"                           : 0x43,
    "SOUND_MONKEYS"                        : 0x44,
    "SOUND_PLANE_CRASHING"                 : 0x45,
    "SOUND_PLANE_ENGINE_SPUTTERING"        : 0x46,
    "SOUND_MAGLEV_2"                       : 0x47,
    "SOUND_DISTANT_BIRD"                   : 0x48,

    # sprite ids
    "SPRITE_ID_NEW_TRAIN"    : 0xFD,
    "SPRITE_ID_NEW_ROADVEH"  : 0xFF,
    "SPRITE_ID_NEW_SHIP"     : 0xFF,
    "SPRITE_ID_NEW_AIRCRAFT" : 0xFF,

    "NEW_CARGO_SPRITE"       : 0xFFFF,

    # aircraft type
    "AIRCRAFT_TYPE_HELICOPTER" : 0x00,
    "AIRCRAFT_TYPE_SMALL"      : 0x02,
    "AIRCRAFT_TYPE_LARGE"      : 0x03,

    # ground sprite IDs
    "GROUNDSPRITE_CONCRETE"    : 1420,
    "GROUNDSPRITE_CLEARED"     : 3924,
    "GROUNDSPRITE_GRASS_1_3"   : 3943,
    "GROUNDSPRITE_GRASS_2_3"   : 3962,
    "GROUNDSPRITE_GRASS_3_3"   : 3981,
    "GROUNDSPRITE_GRASS"       : 3981,
    "GROUNDSPRITE_NORMAL"      : 3981,
    "GROUNDSPRITE_WATER"       : 4061,
    "GROUNDSPRITE_SNOW_1_4"    : 4493,
    "GROUNDSPRITE_SNOW_2_4"    : 4512,
    "GROUNDSPRITE_SNOW_3_4"    : 4531,
    "GROUNDSPRITE_SNOW_4_4"    : 4550,
    "GROUNDSPRITE_SNOW"        : 4550,
    "GROUNDSPRITE_DESERT_1_2"  : 4512,
    "GROUNDSPRITE_DESERT_2_2"  : 4550,
    "GROUNDSPRITE_DESERT"      : 4550,

    # general CB for rerandomizing
    "CB_RANDOM_TRIGGER"        : 0x01,

    # house flags
    "HOUSE_FLAG_NOT_SLOPED"         : 1,
    "HOUSE_FLAG_ANIMATE"            : 5,
    "HOUSE_FLAG_CHURCH"             : 6,
    "HOUSE_FLAG_STADIUM"            : 7,
    "HOUSE_FLAG_ONLY_SE"            : 8,
    "HOUSE_FLAG_PROTECTED"          : 9,
    "HOUSE_FLAG_SYNC_CALLBACK"      : 10,
    "HOUSE_FLAG_RANDOM_ANIMATION"   : 11,

    # cargo acceptance
    "HOUSE_ACCEPT_GOODS"            : 0x00,
    "HOUSE_ACCEPT_FOOD"             : 0x10,  # 0x80 / 8
    "HOUSE_ACCEPT_FIZZY_DRINKS"     : 0x10,  # 0x80 / 8

    # house sizes
    "HOUSE_SIZE_1X1"                : 0,
    "HOUSE_SIZE_2X1"                : 2,
    "HOUSE_SIZE_1X2"                : 3,
    "HOUSE_SIZE_2X2"                : 4,

    # house tiles
    "HOUSE_TILE_NORTH"              : 0,
    "HOUSE_TILE_EAST"               : 1,
    "HOUSE_TILE_WEST"               : 2,
    "HOUSE_TILE_SOUTH"              : 3,

    # house callback results
    "CB_RESULT_HOUSE_NO_MORE_PRODUCTION": 0x20FF,

    # town zones
    "TOWNZONE_EDGE"                 : 0,
    "TOWNZONE_OUTSKIRT"             : 1,
    "TOWNZONE_OUTER_SUBURB"         : 2,
    "TOWNZONE_INNER_SUBURB"         : 3,
    "TOWNZONE_CENTRE"               : 4,
    "ALL_TOWNZONES"                 : 0x1F,

    # industry tile special flags
    "INDTILE_FLAG_RANDOM_ANIMATION"   : 0,
    "INDTILE_FLAG_ACCEPT_ALL"         : 1,

    "CB_RESULT_IND_PROD_NO_CHANGE"      : 0x00,
    "CB_RESULT_IND_PROD_HALF"           : 0x01,
    "CB_RESULT_IND_PROD_DOUBLE"         : 0x02,
    "CB_RESULT_IND_PROD_CLOSE"          : 0x03,
    "CB_RESULT_IND_PROD_RANDOM"         : 0x04,
    "CB_RESULT_IND_PROD_DIVIDE_BY_4"    : 0x05,
    "CB_RESULT_IND_PROD_DIVIDE_BY_8"    : 0x06,
    "CB_RESULT_IND_PROD_DIVIDE_BY_16"   : 0x07,
    "CB_RESULT_IND_PROD_DIVIDE_BY_32"   : 0x08,
    "CB_RESULT_IND_PROD_MULTIPLY_BY_4"  : 0x09,
    "CB_RESULT_IND_PROD_MULTIPLY_BY_8"  : 0x0A,
    "CB_RESULT_IND_PROD_MULTIPLY_BY_16" : 0x0B,
    "CB_RESULT_IND_PROD_MULTIPLY_BY_32" : 0x0C,
    "CB_RESULT_IND_PROD_DECREMENT_BY_1" : 0x0D,
    "CB_RESULT_IND_PROD_INCREMENT_BY_1" : 0x0E,
    "CB_RESULT_IND_PROD_SET_BY_0x100"   : 0x0F,

    "CB_RESULT_IND_DO_NOT_USE_SPECIAL"  : 0x00,
    "CB_RESULT_IND_USE_SPECIAL"         : 0x01,

    "CB_RESULT_IND_NO_CONSTRUCTION"            : 0x0000,
    "CB_RESULT_IND_PROBABILITY_FROM_PROPERTY"  : 0x0100,

    "CB_RESULT_NO_TEXT"                 : 0x400,
    "CB_RESULT_IND_NO_TEXT_NO_AMOUNT"   : 0x401,

    "CB_RESULT_LOCATION_ALLOW"                        : 0x400,
    "CB_RESULT_LOCATION_DISALLOW"                     : 0x401,
    "CB_RESULT_LOCATION_DISALLOW_ONLY_RAINFOREST"     : 0x402,
    "CB_RESULT_LOCATION_DISALLOW_ONLY_DESERT"         : 0x403,
    "CB_RESULT_LOCATION_DISALLOW_ONLY_ABOVE_SNOWLINE" : 0x404,
    "CB_RESULT_LOCATION_DISALLOW_ONLY_BELOW_SNOWLINE" : 0x405,
    "CB_RESULT_LOCATION_DISALLOW_NOT_ON_OPEN_SEA"     : 0x406,
    "CB_RESULT_LOCATION_DISALLOW_NOT_ON_CANAL"        : 0x407,
    "CB_RESULT_LOCATION_DISALLOW_NOT_ON_RIVER"        : 0x408,

    # industry special flags
    "IND_FLAG_PLANT_FIELDS_PERIODICALLY"               : 0,
    "IND_FLAG_CUT_TREES"                               : 1,
    "IND_FLAG_BUILT_ON_WATER"                          : 2,
    "IND_FLAG_ONLY_IN_LARGE_TOWNS"                     : 3,
    "IND_FLAG_ONLY_IN_TOWNS"                           : 4,
    "IND_FLAG_BUILT_NEAR_TOWN"                         : 5,
    "IND_FLAG_PLANT_FIELDS_WHEN_BUILT"                 : 6,
    "IND_FLAG_NO_PRODUCTION_INCREASE"                  : 7,
    "IND_FLAG_BUILT_ONLY_BEFORE_1950"                  : 8,
    "IND_FLAG_BUILT_ONLY_AFTER_1960"                   : 9,
    "IND_FLAG_AI_CREATES_AIR_AND_SHIP_ROUTES"          : 10,
    "IND_FLAG_MILITARY_AIRPLANE_CAN_EXPLODE"           : 11,
    "IND_FLAG_MILITARY_HELICOPTER_CAN_EXPLODE"         : 12,
    "IND_FLAG_CAN_CAUSE_SUBSIDENCE"                    : 13,
    "IND_FLAG_AUTOMATIC_PRODUCTION_MULTIPLIER"         : 14,
    "IND_FLAG_RANDOM_BITS_IN_PRODUCTION_CALLBACK"      : 15,
    "IND_FLAG_DO_NOT_FORCE_INSTANCE_AT_MAP_GENERATION" : 16,
    "IND_FLAG_ALLOW_CLOSING_LAST_INSTANCE"             : 17,
    "IND_FLAG_LONG_CARGO_TYPE_LISTS"                   : 18,
    "IND_FLAG_DO_NOT_CLAMP_PASSENGER_PRODUCTION"       : 19,

    # flags for builtin function industry_type(..)
    "IND_TYPE_OLD"             : 0,
    "IND_TYPE_NEW"             : 1,

    # founder for industries (founder variable)
    "FOUNDER_GAME"             : 16,

    # object flags
    "OBJ_FLAG_ONLY_SE"         : 0,
    "OBJ_FLAG_IRREMOVABLE"     : 1,
    "OBJ_FLAG_ANYTHING_REMOVE" : 2,
    "OBJ_FLAG_ON_WATER"        : 3,
    "OBJ_FLAG_REMOVE_IS_INCOME": 4,
    "OBJ_FLAG_NO_FOUNDATIONS"  : 5,
    "OBJ_FLAG_ANIMATED"        : 6,
    "OBJ_FLAG_ONLY_INGAME"     : 7,
    "OBJ_FLAG_2CC"             : 8,
    "OBJ_FLAG_NOT_ON_LAND"     : 9,
    "OBJ_FLAG_DRAW_WATER"      : 10,
    "OBJ_FLAG_ALLOW_BRIDGE"    : 11,
    "OBJ_FLAG_RANDOM_ANIMATION": 12,
    "OBJ_FLAG_SCALE_BY_WATER"  : 13,

    # object animation triggers
    "OBJ_ANIM_IS_BUILT"        : 0,
    "OBJ_ANIM_PERIODIC"        : 1,
    "OBJ_ANIM_SYNC"            : 2,

    # Special values for object var 0x60
    "OBJECT_TYPE_OTHER_GRF"     : 0xFFFE,
    "OBJECT_TYPE_NO_OBJECT"     : 0xFFFF,

    # railtype flags
    "RAILTYPE_FLAG_CATENARY"          : 0,
    "RAILTYPE_FLAG_NO_LEVEL_CROSSING" : 1,  # for OpenTTD > r20049
    "RAILTYPE_FLAG_HIDDEN"            : 2,
    "RAILTYPE_FLAG_PRECOMBINED"       : 3,
    "RAILTYPE_FLAG_ALLOW_90DEG"       : 4,
    "RAILTYPE_FLAG_DISALLOW_90DEG"    : 5,

    # roadtype flags
    "ROADTYPE_FLAG_CATENARY"          : 0,
    "ROADTYPE_FLAG_NO_LEVEL_CROSSING" : 1,
    "ROADTYPE_FLAG_NO_HOUSES"         : 2,
    "ROADTYPE_FLAG_HIDDEN"            : 3,
    "ROADTYPE_FLAG_TOWN_BUILD"        : 4,

    # tramtype flags
    "TRAMTYPE_FLAG_CATENARY"          : 0,
    "TRAMTYPE_FLAG_NO_LEVEL_CROSSING" : 1,
    "TRAMTYPE_FLAG_NO_HOUSES"         : 2,
    "TRAMTYPE_FLAG_HIDDEN"            : 3,
    "TRAMTYPE_FLAG_TOWN_BUILD"        : 4,

    # type of default station graphics used for a railtype
    "RAILTYPE_STATION_NORMAL"   : 0,
    "RAILTYPE_STATION_MONORAIL" : 1,
    "RAILTYPE_STATION_MAGLEV"   : 2,

    # ground tile types as returned by railtypes varaction2 0x40
    "TILETYPE_NORMAL"           : 0x00,
    "TILETYPE_DESERT"           : 0x01,
    "TILETYPE_RAIN_FOREST"      : 0x02,
    "TILETYPE_SNOW"             : 0x04,

    # Water classes
    "WATER_CLASS_NONE"          : 0,
    "WATER_CLASS_SEA"           : 1,
    "WATER_CLASS_CANAL"         : 2,
    "WATER_CLASS_RIVER"         : 3,

    # level crossing status as returned by railtypes varaction2 0x42
    "LEVEL_CROSSING_CLOSED"     : 1,
    "LEVEL_CROSSING_OPEN"       : 0,
    "LEVEL_CROSSING_NONE"       : 0,

    # acceleration model for trains
    "ACC_MODEL_RAIL"     : 0,
    "ACC_MODEL_MONORAIL" : 1,
    "ACC_MODEL_MAGLEV"   : 2,

    # default industry IDs
    "INDUSTRYTYPE_COAL_MINE"             : 0x00,
    "INDUSTRYTYPE_POWER_PLANT"           : 0x01,
    "INDUSTRYTYPE_SAWMILL"               : 0x02,
    "INDUSTRYTYPE_FOREST"                : 0x03,
    "INDUSTRYTYPE_OIL_REFINERY"          : 0x04,
    "INDUSTRYTYPE_OIL_RIG"               : 0x05,
    "INDUSTRYTYPE_TEMPERATE_FACTORY"     : 0x06,
    "INDUSTRYTYPE_PRINTING_WORKS"        : 0x07,
    "INDUSTRYTYPE_STEEL_MILL"            : 0x08,
    "INDUSTRYTYPE_TEMPERATE_ARCTIC_FARM" : 0x09,
    "INDUSTRYTYPE_COPPER_ORE_MINE"       : 0x0A,
    "INDUSTRYTYPE_OIL_WELLS"             : 0x0B,
    "INDUSTRYTYPE_TEMPERATE_BANK"        : 0x0C,
    "INDUSTRYTYPE_FOOD_PROCESSING_PLANT" : 0x0D,
    "INDUSTRYTYPE_PAPER_MILL"            : 0x0E,
    "INDUSTRYTYPE_GOLD_MINE"             : 0x0F,
    "INDUSTRYTYPE_TROPICAL_ARCTIC_BANK"  : 0x10,
    "INDUSTRYTYPE_DIAMOND_MINE"          : 0x11,
    "INDUSTRYTYPE_IRON_ORE_MINE"         : 0x12,
    "INDUSTRYTYPE_FRUIT_PLANTATION"      : 0x13,
    "INDUSTRYTYPE_RUBBER_PLANTATION"     : 0x14,
    "INDUSTRYTYPE_WATER_WELL"            : 0x15,
    "INDUSTRYTYPE_WATER_TOWER"           : 0x16,
    "INDUSTRYTYPE_TROPICAL_FACTORY"      : 0x17,
    "INDUSTRYTYPE_TROPICAL_FARM"         : 0x18,
    "INDUSTRYTYPE_LUMBER_MILL"           : 0x19,
    "INDUSTRYTYPE_CANDYFLOSS_FOREST"     : 0x1A,
    "INDUSTRYTYPE_SWEETS_FACTORY"        : 0x1B,
    "INDUSTRYTYPE_BATTERY_FARM"          : 0x1C,
    "INDUSTRYTYPE_COLA_WELLS"            : 0x1D,
    "INDUSTRYTYPE_TOY_SHOP"              : 0x1E,
    "INDUSTRYTYPE_TOY_FACTORY"           : 0x1F,
    "INDUSTRYTYPE_PLASTIC_FOUNTAIN"      : 0x20,
    "INDUSTRYTYPE_FIZZY_DRINKS_FACTORY"  : 0x21,
    "INDUSTRYTYPE_BUBBLE_GENERATOR"      : 0x22,
    "INDUSTRYTYPE_TOFFE_QUARRY"          : 0x23,
    "INDUSTRYTYPE_SUGAR_MINE"            : 0x24,

    "INDUSTRYTYPE_UNKNOWN"               : 0xFE,
    "INDUSTRYTYPE_TOWN"                  : 0xFF,

    # industry life types (industry property 0x0B, life_type)
    "IND_LIFE_TYPE_BLACK_HOLE"           : 0x00,
    "IND_LIFE_TYPE_EXTRACTIVE"           : 0x01,
    "IND_LIFE_TYPE_ORGANIC"              : 0x02,
    "IND_LIFE_TYPE_PROCESSING"           : 0x04,

    # traffic side (bool, true = right hand side)
    "TRAFFIC_SIDE_LEFT"                  : 0,
    "TRAFFIC_SIDE_RIGHT"                 : 1,

    # which platform has loaded this grf
    "PLATFORM_TTDPATCH"                  : 0x00,
    "PLATFORM_OPENTTD"                   : 0x01,

    # player types (vehicle var 0x43)
    "PLAYERTYPE_HUMAN"                   : 0,
    "PLAYERTYPE_AI"                      : 1,
    "PLAYERTYPE_HUMAN_IN_AI"             : 2,
    "PLAYERTYPE_AI_IN_HUMAN"             : 3,

    # search criteria for house var 0x65
    "SEARCH_HOUSE_BY_TYPE"               : 0,
    "SEARCH_HOUSE_BY_CLASS"              : 1,
    "SEARCH_HOUSE_BY_GRFID"              : 2,

    # build types (industry var 0xB3)
    "BUILDTYPE_UNKNOWN"                  : 0,
    "BUILDTYPE_GAMEPLAY"                 : 1,
    "BUILDTYPE_GENERATION"               : 2,
    "BUILDTYPE_EDITOR"                   : 3,

    # Creation types (several industry[tile] callbacks
    "IND_CREATION_GENERATION"            : 0,
    "IND_CREATION_RANDOM"                : 1,
    "IND_CREATION_FUND"                  : 2,
    "IND_CREATION_PROSPECT"              : 3,

    # airport types (vehicle var 0x44, base station var airport_type)
    "AIRPORTTYPE_SMALL"                  : 0,
    "AIRPORTTYPE_LARGE"                  : 1,
    "AIRPORTTYPE_HELIPORT"               : 2,
    "AIRPORTTYPE_OILRIG"                 : 3,

    # Direction for e.g. airport layouts, vehicle direction
    "DIRECTION_NORTH"                     : 0,
    "DIRECTION_NORTHEAST"                 : 1,
    "DIRECTION_EAST"                      : 2,
    "DIRECTION_SOUTHEAST"                 : 3,
    "DIRECTION_SOUTH"                     : 4,
    "DIRECTION_SOUTHWEST"                 : 5,
    "DIRECTION_WEST"                      : 6,
    "DIRECTION_NORTHWEST"                 : 7,

    "CANAL_DIRECTION_NORTH"               : 7,
    "CANAL_DIRECTION_NORTHEAST"           : 0,
    "CANAL_DIRECTION_EAST"                : 4,
    "CANAL_DIRECTION_SOUTHEAST"           : 1,
    "CANAL_DIRECTION_SOUTH"               : 5,
    "CANAL_DIRECTION_SOUTHWEST"           : 2,
    "CANAL_DIRECTION_WEST"                : 6,
    "CANAL_DIRECTION_NORTHWEST"           : 3,

    "CORNER_W"                            : 0,
    "CORNER_S"                            : 1,
    "CORNER_E"                            : 2,
    "CORNER_N"                            : 3,
    "IS_STEEP_SLOPE"                      : 4,

    "SLOPE_FLAT"                          : 0,
    "SLOPE_W"                             : 1,
    "SLOPE_S"                             : 2,
    "SLOPE_E"                             : 4,
    "SLOPE_N"                             : 8,
    "SLOPE_NW"                            : 9,
    "SLOPE_SW"                            : 3,
    "SLOPE_SE"                            : 6,
    "SLOPE_NE"                            : 12,
    "SLOPE_EW"                            : 5,
    "SLOPE_NS"                            : 10,
    "SLOPE_NWS"                           : 11,
    "SLOPE_WSE"                           : 7,
    "SLOPE_SEN"                           : 14,
    "SLOPE_ENW"                           : 13,
    "SLOPE_STEEP_W"                       : 27,
    "SLOPE_STEEP_S"                       : 23,
    "SLOPE_STEEP_E"                       : 30,
    "SLOPE_STEEP_N"                       : 29,

    # loading stages
    "LOADING_STAGE_INITIALIZE"            : 0x0000,
    "LOADING_STAGE_RESERVE"               : 0x0101,
    "LOADING_STAGE_ACTIVATE"              : 0x0201,
    "LOADING_STAGE_TEST"                  : 0x0401,

    # palettes
    "PALETTE_DOS"                           : 0,
    "PALETTE_DEFAULT"                       : 0,
    "PALETTE_WIN"                           : 1,
    "PALETTE_LEGACY"                        : 1,

    # game mode
    "GAMEMODE_MENU"                         : 0,
    "GAMEMODE_GAME"                         : 1,
    "GAMEMODE_EDITOR"                       : 2,

    # difficulty
    "DIFFICULTY_EASY"                       : 0,
    "DIFFICULTY_MEDIUM"                     : 1,
    "DIFFICULTY_HARD"                       : 2,
    "DIFFICULTY_CUSTOM"                     : 3,

    # display options
    "DISPLAY_TOWN_NAMES"                    : 0,
    "DISPLAY_STATION_NAMES"                 : 1,
    "DISPLAY_SIGNS"                         : 2,
    "DISPLAY_ANIMATION"                     : 3,
    "DISPLAY_FULL_DETAIL"                   : 5,

    # map types (ttdp variable 0x13)
    "MAP_TYPE_X_BIGGER"                     : 0,  # bit 0 and 1 clear
    "MAP_TYPE_RECTANGULAR"                  : "MAP_TYPE_SQUARE",
    "MAP_TYPE_SQUARE"                       : 1,  # bit 0 set
    "MAP_TYPE_Y_BIGGER"                     : 2,  # bit 0 clear, bit 1 set

    # Platform types (platform_xx station variables)
    "PLATFORM_SAME_STATION"                 : 0,
    "PLATFORM_SAME_SECTION"                 : 1,
    "PLATFORM_SAME_DIRECTION"               : 2,

    # vehicle type (base station var "had_vehicle_of_type")
    "HAD_VEHICLE_OF_TYPE_TRAIN"             : 0,
    "HAD_VEHICLE_OF_TYPE_BUS"               : 1,
    "HAD_VEHICLE_OF_TYPE_TRUCK"             : 2,
    "HAD_VEHICLE_OF_TYPE_AIRCRAFT"          : 3,
    "HAD_VEHICLE_OF_TYPE_SHIP"              : 4,

    # station facilities (base station var "facilities")
    "FACILITY_TRAIN"                        : 0,
    "FACILITY_TRUCK_STOP"                   : 1,
    "FACILITY_BUS_STOP"                     : 2,
    "FACILITY_AIRPORT"                      : 3,
    "FACILITY_DOCK"                         : 4,

    # Random triggers
    "TRIGGER_ALL_NEEDED"                    : 7,

    "TRIGGER_VEHICLE_NEW_LOAD"              : 0,
    "TRIGGER_VEHICLE_SERVICE"               : 1,
    "TRIGGER_VEHICLE_UNLOAD_ALL"            : 2,
    "TRIGGER_VEHICLE_ANY_LOAD"              : 3,
    "TRIGGER_VEHICLE_32_CALLBACK"           : 4,

    "TRIGGER_STATION_NEW_CARGO"             : 0,
    "TRIGGER_STATION_NO_MORE_CARGO"         : 1,
    "TRIGGER_STATION_TRAIN_ARRIVES"         : 2,
    "TRIGGER_STATION_TRAIN_LEAVES"          : 3,
    "TRIGGER_STATION_TRAIN_LOADS_UNLOADS"   : 4,
    "TRIGGER_STATION_TRAIN_RESERVES"        : 5,

    "TRIGGER_HOUSE_TILELOOP"                : 0,
    "TRIGGER_HOUSE_TOP_TILELOOP"            : 1,

    "TRIGGER_INDUSTRYTILE_TILELOOP"         : 0,
    "TRIGGER_INDUSTRYTILE_256_TICKS"        : 1,
    "TRIGGER_INDUSTRYTILE_CARGO_DELIVERY"   : 2,

    # Tile classes
    "TILE_CLASS_GROUND"                     : 0x00,
    "TILE_CLASS_RAIL"                       : 0x01,
    "TILE_CLASS_ROAD"                       : 0x02,
    "TILE_CLASS_HOUSE"                      : 0x03,
    "TILE_CLASS_TREES"                      : 0x04,
    "TILE_CLASS_STATION"                    : 0x05,
    "TILE_CLASS_WATER"                      : 0x06,
    "TILE_CLASS_VOID"                       : 0x07,
    "TILE_CLASS_INDUSTRY"                   : 0x08,
    "TILE_CLASS_TUNNEL_BRIDGE"              : 0x09,
    "TILE_CLASS_OBJECTS"                    : 0x0A,

    # Land shape flags for industry tiles
    "LSF_CANNOT_LOWER_NW_EDGE"              : 0,
    "LSF_CANNOT_LOWER_NE_EDGE"              : 1,
    "LSF_CANNOT_LOWER_SW_EDGE"              : 2,
    "LSF_CANNOT_LOWER_SE_EDGE"              : 3,
    "LSF_ONLY_ON_FLAT_LAND"                 : 4,
    "LSF_ALLOW_ON_WATER"                    : 5,

    # Animation triggers
    "ANIM_TRIGGER_INDTILE_CONSTRUCTION_STATE" : 0,
    "ANIM_TRIGGER_INDTILE_TILE_LOOP"          : 1,
    "ANIM_TRIGGER_INDTILE_INDUSTRY_LOOP"      : 2,
    "ANIM_TRIGGER_INDTILE_RECEIVED_CARGO"     : 3,
    "ANIM_TRIGGER_INDTILE_DISTRIBUTES_CARGO"  : 4,

    "ANIM_TRIGGER_OBJ_BUILT"                : 0,
    "ANIM_TRIGGER_OBJ_TILELOOP"             : 1,
    "ANIM_TRIGGER_OBJ_256_TICKS"            : 2,

    "ANIM_TRIGGER_APT_BUILT"                : 0,
    "ANIM_TRIGGER_APT_TILELOOP"             : 1,
    "ANIM_TRIGGER_APT_NEW_CARGO"            : 2,
    "ANIM_TRIGGER_APT_CARGO_TAKEN"          : 3,
    "ANIM_TRIGGER_APT_250_TICKS"            : 4,
    "ANIM_TRIGGER_APT_AIRPLANE_LANDS"       : 5,

    # Animation looping
    "ANIMATION_NON_LOOPING"                 : 0,
    "ANIMATION_LOOPING"                     : 1,

    # Animation callback results
    "CB_RESULT_STOP_ANIMATION"              : 0xFF,  # callback 0x25, 0x26
    "CB_RESULT_START_ANIMATION"             : 0xFE,  # callback 0x25
    "CB_RESULT_NEXT_FRAME"                  : 0xFE,  # callback 0x26
    "CB_RESULT_DO_NOTHING"                  : 0xFD,  # callback 0x25

    "CB_RESULT_FOUNDATIONS"                 : 0x01,  # callback 0x30
    "CB_RESULT_NO_FOUNDATIONS"              : 0x00,  # callback 0x30

    "CB_RESULT_AUTOSLOPE"                   : 0x00,  # callback 0x3C
    "CB_RESULT_NO_AUTOSLOPE"                : 0x01,  # callback 0x3C

    # Recolour modes for layout sprites
    "RECOLOUR_NONE"                         : 0,
    "RECOLOUR_TRANSPARENT"                  : 1,
    "RECOLOUR_REMAP"                        : 2,

    # Possible values for palette
    "PALETTE_USE_DEFAULT"                   : 0,
    "PALETTE_TILE_RED_PULSATING"            : 771,
    "PALETTE_SEL_TILE_RED"                  : 772,
    "PALETTE_SEL_TILE_BLUE"                 : 773,
    "PALETTE_IDENTITY"                      : 775,
    "PALETTE_CC_FIRST"                      : 775,
    "PALETTE_CC_DARK_BLUE"                  : 775,  # = first
    "PALETTE_CC_PALE_GREEN"                 : 776,
    "PALETTE_CC_PINK"                       : 777,
    "PALETTE_CC_YELLOW"                     : 778,
    "PALETTE_CC_RED"                        : 779,
    "PALETTE_CC_LIGHT_BLUE"                 : 780,
    "PALETTE_CC_GREEN"                      : 781,
    "PALETTE_CC_DARK_GREEN"                 : 782,
    "PALETTE_CC_BLUE"                       : 783,
    "PALETTE_CC_CREAM"                      : 784,
    "PALETTE_CC_MAUVE"                      : 785,
    "PALETTE_CC_PURPLE"                     : 786,
    "PALETTE_CC_ORANGE"                     : 787,
    "PALETTE_CC_BROWN"                      : 788,
    "PALETTE_CC_GREY"                       : 789,
    "PALETTE_CC_WHITE"                      : 790,
    "PALETTE_BARE_LAND"                     : 791,
    "PALETTE_STRUCT_BLUE"                   : 795,
    "PALETTE_STRUCT_BROWN"                  : 796,
    "PALETTE_STRUCT_WHITE"                  : 797,
    "PALETTE_STRUCT_RED"                    : 798,
    "PALETTE_STRUCT_GREEN"                  : 799,
    "PALETTE_STRUCT_CONCRETE"               : 800,
    "PALETTE_STRUCT_YELLOW"                 : 801,
    "PALETTE_TRANSPARENT"                   : 802,
    "PALETTE_STRUCT_GREY"                   : 803,
    "PALETTE_CRASH"                         : 804,
    "PALETTE_CHURCH_RED"                    : 1438,
    "PALETTE_CHURCH_CREAM"                  : 1439,

    # Company colours
    "COLOUR_DARK_BLUE"                      : 0,
    "COLOUR_PALE_GREEN"                     : 1,
    "COLOUR_PINK"                           : 2,
    "COLOUR_YELLOW"                         : 3,
    "COLOUR_RED"                            : 4,
    "COLOUR_LIGHT_BLUE"                     : 5,
    "COLOUR_GREEN"                          : 6,
    "COLOUR_DARK_GREEN"                     : 7,
    "COLOUR_BLUE"                           : 8,
    "COLOUR_CREAM"                          : 9,
    "COLOUR_MAUVE"                          : 10,
    "COLOUR_PURPLE"                         : 11,
    "COLOUR_ORANGE"                         : 12,
    "COLOUR_BROWN"                          : 13,
    "COLOUR_GREY"                           : 14,
    "COLOUR_WHITE"                          : 15,

    # Town growth effect of cargo
    "TOWNGROWTH_PASSENGERS"                 : 0x00,
    "TOWNGROWTH_MAIL"                       : 0x02,
    "TOWNGROWTH_GOODS"                      : 0x05,
    "TOWNGROWTH_WATER"                      : 0x09,
    "TOWNGROWTH_FOOD"                       : 0x0B,
    "TOWNGROWTH_NONE"                       : 0xFF,

    # Cargo callbacks
    "CARGO_CB_PROFIT"                       : 0x01,
    "CARGO_CB_STATION_RATING"               : 0x02,

    # CMP and UCMP results
    "CMP_LESS"                              : 0,
    "CMP_EQUAL"                             : 1,
    "CMP_GREATER"                           : 2,

    # TTD Strings
    "TTD_STR_CARGO_PLURAL_NOTHING"                          : 0x000E,
    "TTD_STR_CARGO_PLURAL_PASSENGERS"                       : 0x000F,
    "TTD_STR_CARGO_PLURAL_COAL"                             : 0x0010,
    "TTD_STR_CARGO_PLURAL_MAIL"                             : 0x0011,
    "TTD_STR_CARGO_PLURAL_OIL"                              : 0x0012,
    "TTD_STR_CARGO_PLURAL_LIVESTOCK"                        : 0x0013,
    "TTD_STR_CARGO_PLURAL_GOODS"                            : 0x0014,
    "TTD_STR_CARGO_PLURAL_GRAIN"                            : 0x0015,
    "TTD_STR_CARGO_PLURAL_WOOD"                             : 0x0016,
    "TTD_STR_CARGO_PLURAL_IRON_ORE"                         : 0x0017,
    "TTD_STR_CARGO_PLURAL_STEEL"                            : 0x0018,
    "TTD_STR_CARGO_PLURAL_VALUABLES"                        : 0x0019,
    "TTD_STR_CARGO_PLURAL_COPPER_ORE"                       : 0x001A,
    "TTD_STR_CARGO_PLURAL_MAIZE"                            : 0x001B,
    "TTD_STR_CARGO_PLURAL_FRUIT"                            : 0x001C,
    "TTD_STR_CARGO_PLURAL_DIAMONDS"                         : 0x001D,
    "TTD_STR_CARGO_PLURAL_FOOD"                             : 0x001E,
    "TTD_STR_CARGO_PLURAL_PAPER"                            : 0x001F,
    "TTD_STR_CARGO_PLURAL_GOLD"                             : 0x0020,
    "TTD_STR_CARGO_PLURAL_WATER"                            : 0x0021,
    "TTD_STR_CARGO_PLURAL_WHEAT"                            : 0x0022,
    "TTD_STR_CARGO_PLURAL_RUBBER"                           : 0x0023,
    "TTD_STR_CARGO_PLURAL_SUGAR"                            : 0x0024,
    "TTD_STR_CARGO_PLURAL_TOYS"                             : 0x0025,
    "TTD_STR_CARGO_PLURAL_CANDY"                            : "TTD_STR_CARGO_PLURAL_SWEETS",
    "TTD_STR_CARGO_PLURAL_SWEETS"                           : 0x0026,
    "TTD_STR_CARGO_PLURAL_COLA"                             : 0x0027,
    "TTD_STR_CARGO_PLURAL_COTTON_CANDY"                     : "TTD_STR_CARGO_PLURAL_CANDYFLOSS",
    "TTD_STR_CARGO_PLURAL_CANDYFLOSS"                       : 0x0028,
    "TTD_STR_CARGO_PLURAL_BUBBLES"                          : 0x0029,
    "TTD_STR_CARGO_PLURAL_TOFFEE"                           : 0x002A,
    "TTD_STR_CARGO_PLURAL_BATTERIES"                        : 0x002B,
    "TTD_STR_CARGO_PLURAL_PLASTIC"                          : 0x002C,
    "TTD_STR_CARGO_PLURAL_FIZZY_DRINKS"                     : 0x002D,
    "TTD_STR_CARGO_SINGULAR_NOTHING"                        : 0x002E,
    "TTD_STR_CARGO_SINGULAR_PASSENGER"                      : 0x002F,
    "TTD_STR_CARGO_SINGULAR_COAL"                           : 0x0030,
    "TTD_STR_CARGO_SINGULAR_MAIL"                           : 0x0031,
    "TTD_STR_CARGO_SINGULAR_OIL"                            : 0x0032,
    "TTD_STR_CARGO_SINGULAR_LIVESTOCK"                      : 0x0033,
    "TTD_STR_CARGO_SINGULAR_GOODS"                          : 0x0034,
    "TTD_STR_CARGO_SINGULAR_GRAIN"                          : 0x0035,
    "TTD_STR_CARGO_SINGULAR_WOOD"                           : 0x0036,
    "TTD_STR_CARGO_SINGULAR_IRON_ORE"                       : 0x0037,
    "TTD_STR_CARGO_SINGULAR_STEEL"                          : 0x0038,
    "TTD_STR_CARGO_SINGULAR_VALUABLES"                      : 0x0039,
    "TTD_STR_CARGO_SINGULAR_COPPER_ORE"                     : 0x003A,
    "TTD_STR_CARGO_SINGULAR_MAIZE"                          : 0x003B,
    "TTD_STR_CARGO_SINGULAR_FRUIT"                          : 0x003C,
    "TTD_STR_CARGO_SINGULAR_DIAMOND"                        : 0x003D,
    "TTD_STR_CARGO_SINGULAR_FOOD"                           : 0x003E,
    "TTD_STR_CARGO_SINGULAR_PAPER"                          : 0x003F,
    "TTD_STR_CARGO_SINGULAR_GOLD"                           : 0x0040,
    "TTD_STR_CARGO_SINGULAR_WATER"                          : 0x0041,
    "TTD_STR_CARGO_SINGULAR_WHEAT"                          : 0x0042,
    "TTD_STR_CARGO_SINGULAR_RUBBER"                         : 0x0043,
    "TTD_STR_CARGO_SINGULAR_SUGAR"                          : 0x0044,
    "TTD_STR_CARGO_SINGULAR_TOY"                            : 0x0045,
    "TTD_STR_CARGO_SINGULAR_CANDY"                          : "TTD_STR_CARGO_SINGULAR_SWEETS",
    "TTD_STR_CARGO_SINGULAR_SWEETS"                         : 0x0046,
    "TTD_STR_CARGO_SINGULAR_COLA"                           : 0x0047,
    "TTD_STR_CARGO_SINGULAR_COTTON_CANDY"                   : "TTD_STR_CARGO_SINGULAR_CANDYFLOSS",
    "TTD_STR_CARGO_SINGULAR_CANDYFLOSS"                     : 0x0048,
    "TTD_STR_CARGO_SINGULAR_BUBBLE"                         : 0x0049,
    "TTD_STR_CARGO_SINGULAR_TOFFEE"                         : 0x004A,
    "TTD_STR_CARGO_SINGULAR_BATTERY"                        : 0x004B,
    "TTD_STR_CARGO_SINGULAR_PLASTIC"                        : 0x004C,
    "TTD_STR_CARGO_SINGULAR_FIZZY_DRINK"                    : 0x004D,
    "TTD_STR_PASSENGERS"                                    : 0x004F,
    "TTD_STR_TONS"                                          : 0x0050,
    "TTD_STR_BAGS"                                          : 0x0051,
    "TTD_STR_LITERS"                                        : 0x0052,
    "TTD_STR_ITEMS"                                         : 0x0053,
    "TTD_STR_CRATES"                                        : 0x0054,
    "TTD_STR_QUANTITY_NOTHING"                              : 0x006E,
    "TTD_STR_QUANTITY_PASSENGERS"                           : 0x006F,
    "TTD_STR_QUANTITY_COAL"                                 : 0x0070,
    "TTD_STR_QUANTITY_MAIL"                                 : 0x0071,
    "TTD_STR_QUANTITY_OIL"                                  : 0x0072,
    "TTD_STR_QUANTITY_LIVESTOCK"                            : 0x0073,
    "TTD_STR_QUANTITY_GOODS"                                : 0x0074,
    "TTD_STR_QUANTITY_GRAIN"                                : 0x0075,
    "TTD_STR_QUANTITY_WOOD"                                 : 0x0076,
    "TTD_STR_QUANTITY_IRON_ORE"                             : 0x0077,
    "TTD_STR_QUANTITY_STEEL"                                : 0x0078,
    "TTD_STR_QUANTITY_VALUABLES"                            : 0x0079,
    "TTD_STR_QUANTITY_COPPER_ORE"                           : 0x007A,
    "TTD_STR_QUANTITY_MAIZE"                                : 0x007B,
    "TTD_STR_QUANTITY_FRUIT"                                : 0x007C,
    "TTD_STR_QUANTITY_DIAMONDS"                             : 0x007D,
    "TTD_STR_QUANTITY_FOOD"                                 : 0x007E,
    "TTD_STR_QUANTITY_PAPER"                                : 0x007F,
    "TTD_STR_QUANTITY_GOLD"                                 : 0x0080,
    "TTD_STR_QUANTITY_WATER"                                : 0x0081,
    "TTD_STR_QUANTITY_WHEAT"                                : 0x0082,
    "TTD_STR_QUANTITY_RUBBER"                               : 0x0083,
    "TTD_STR_QUANTITY_SUGAR"                                : 0x0084,
    "TTD_STR_QUANTITY_TOYS"                                 : 0x0085,
    "TTD_STR_QUANTITY_SWEETS"                               : 0x0086,
    "TTD_STR_QUANTITY_COLA"                                 : 0x0087,
    "TTD_STR_QUANTITY_CANDYFLOSS"                           : 0x0088,
    "TTD_STR_QUANTITY_BUBBLES"                              : 0x0089,
    "TTD_STR_QUANTITY_TOFFEE"                               : 0x008A,
    "TTD_STR_QUANTITY_BATTERIES"                            : 0x008B,
    "TTD_STR_QUANTITY_PLASTIC"                              : 0x008C,
    "TTD_STR_QUANTITY_FIZZY_DRINKS"                         : 0x008D,
    "TTD_STR_ABBREV_NOTHING"                                : 0x008E,
    "TTD_STR_ABBREV_PASSENGERS"                             : 0x008F,
    "TTD_STR_ABBREV_COAL"                                   : 0x0090,
    "TTD_STR_ABBREV_MAIL"                                   : 0x0091,
    "TTD_STR_ABBREV_OIL"                                    : 0x0092,
    "TTD_STR_ABBREV_LIVESTOCK"                              : 0x0093,
    "TTD_STR_ABBREV_GOODS"                                  : 0x0094,
    "TTD_STR_ABBREV_GRAIN"                                  : 0x0095,
    "TTD_STR_ABBREV_WOOD"                                   : 0x0096,
    "TTD_STR_ABBREV_IRON_ORE"                               : 0x0097,
    "TTD_STR_ABBREV_STEEL"                                  : 0x0098,
    "TTD_STR_ABBREV_VALUABLES"                              : 0x0099,
    "TTD_STR_ABBREV_COPPER_ORE"                             : 0x009A,
    "TTD_STR_ABBREV_MAIZE"                                  : 0x009B,
    "TTD_STR_ABBREV_FRUIT"                                  : 0x009C,
    "TTD_STR_ABBREV_DIAMONDS"                               : 0x009D,
    "TTD_STR_ABBREV_FOOD"                                   : 0x009E,
    "TTD_STR_ABBREV_PAPER"                                  : 0x009F,
    "TTD_STR_ABBREV_GOLD"                                   : 0x00A0,
    "TTD_STR_ABBREV_WATER"                                  : 0x00A1,
    "TTD_STR_ABBREV_WHEAT"                                  : 0x00A2,
    "TTD_STR_ABBREV_RUBBER"                                 : 0x00A3,
    "TTD_STR_ABBREV_SUGAR"                                  : 0x00A4,
    "TTD_STR_ABBREV_TOYS"                                   : 0x00A5,
    "TTD_STR_ABBREV_SWEETS"                                 : 0x00A6,
    "TTD_STR_ABBREV_COLA"                                   : 0x00A7,
    "TTD_STR_ABBREV_CANDYFLOSS"                             : 0x00A8,
    "TTD_STR_ABBREV_BUBBLES"                                : 0x00A9,
    "TTD_STR_ABBREV_TOFFEE"                                 : 0x00AA,
    "TTD_STR_ABBREV_BATTERIES"                              : 0x00AB,
    "TTD_STR_ABBREV_PLASTIC"                                : 0x00AC,
    "TTD_STR_ABBREV_FIZZY_DRINKS"                           : 0x00AD,
    "TTD_STR_TOWN_BUILDING_NAME_TALL_OFFICE_BLOCK_1"        : 0x200F,
    "TTD_STR_TOWN_BUILDING_NAME_OFFICE_BLOCK_1"             : 0x2010,
    "TTD_STR_TOWN_BUILDING_NAME_SMALL_BLOCK_OF_FLATS_1"     : 0x2011,
    "TTD_STR_TOWN_BUILDING_NAME_CHURCH_1"                   : 0x2012,
    "TTD_STR_TOWN_BUILDING_NAME_LARGE_OFFICE_BLOCK_1"       : 0x2013,
    "TTD_STR_TOWN_BUILDING_NAME_TOWN_HOUSES_1"              : 0x2014,
    "TTD_STR_TOWN_BUILDING_NAME_HOTEL_1"                    : 0x2015,
    "TTD_STR_TOWN_BUILDING_NAME_STATUE_1"                   : 0x2016,
    "TTD_STR_TOWN_BUILDING_NAME_FOUNTAIN_1"                 : 0x2017,
    "TTD_STR_TOWN_BUILDING_NAME_PARK_1"                     : 0x2018,
    "TTD_STR_TOWN_BUILDING_NAME_OFFICE_BLOCK_2"             : 0x2019,
    "TTD_STR_TOWN_BUILDING_NAME_SHOPS_AND_OFFICES_1"        : 0x201A,
    "TTD_STR_TOWN_BUILDING_NAME_MODERN_OFFICE_BUILDING_1"   : 0x201B,
    "TTD_STR_TOWN_BUILDING_NAME_WAREHOUSE_1"                : 0x201C,
    "TTD_STR_TOWN_BUILDING_NAME_OFFICE_BLOCK_3"             : 0x201D,
    "TTD_STR_TOWN_BUILDING_NAME_STADIUM_1"                  : 0x201E,
    "TTD_STR_TOWN_BUILDING_NAME_OLD_HOUSES_1"               : 0x201F,
    "TTD_STR_TOWN_BUILDING_NAME_COTTAGES_1"                 : 0x2036,
    "TTD_STR_TOWN_BUILDING_NAME_HOUSES_1"                   : 0x2037,
    "TTD_STR_TOWN_BUILDING_NAME_FLATS_1"                    : 0x2038,
    "TTD_STR_TOWN_BUILDING_NAME_TALL_OFFICE_BLOCK_2"        : 0x2039,
    "TTD_STR_TOWN_BUILDING_NAME_SHOPS_AND_OFFICES_2"        : 0x203A,
    "TTD_STR_TOWN_BUILDING_NAME_SHOPS_AND_OFFICES_3"        : 0x203B,
    "TTD_STR_TOWN_BUILDING_NAME_THEATER_1"                  : 0x203C,
    "TTD_STR_TOWN_BUILDING_NAME_STADIUM_2"                  : 0x203D,
    "TTD_STR_TOWN_BUILDING_NAME_OFFICES_1"                  : 0x203E,
    "TTD_STR_TOWN_BUILDING_NAME_HOUSES_2"                   : 0x203F,
    "TTD_STR_TOWN_BUILDING_NAME_CINEMA_1"                   : 0x2040,
    "TTD_STR_TOWN_BUILDING_NAME_SHOPPING_MALL_1"            : 0x2041,
    "TTD_STR_TOWN_BUILDING_NAME_IGLOO_1"                    : 0x2059,
    "TTD_STR_TOWN_BUILDING_NAME_TEPEES_1"                   : 0x205A,
    "TTD_STR_TOWN_BUILDING_NAME_TEAPOT_HOUSE_1"             : 0x205B,
    "TTD_STR_TOWN_BUILDING_NAME_PIGGY_BANK_1"               : 0x205C,
    "TTD_STR_INDUSTRY_NAME_COAL_MINE"                       : 0x4802,
    "TTD_STR_INDUSTRY_NAME_POWER_STATION"                   : 0x4803,
    "TTD_STR_INDUSTRY_NAME_SAWMILL"                         : 0x4804,
    "TTD_STR_INDUSTRY_NAME_FOREST"                          : 0x4805,
    "TTD_STR_INDUSTRY_NAME_OIL_REFINERY"                    : 0x4806,
    "TTD_STR_INDUSTRY_NAME_OIL_RIG"                         : 0x4807,
    "TTD_STR_INDUSTRY_NAME_FACTORY"                         : 0x4808,
    "TTD_STR_INDUSTRY_NAME_PRINTING_WORKS"                  : 0x4809,
    "TTD_STR_INDUSTRY_NAME_STEEL_MILL"                      : 0x480A,
    "TTD_STR_INDUSTRY_NAME_FARM"                            : 0x480B,
    "TTD_STR_INDUSTRY_NAME_COPPER_ORE_MINE"                 : 0x480C,
    "TTD_STR_INDUSTRY_NAME_OIL_WELLS"                       : 0x480D,
    "TTD_STR_INDUSTRY_NAME_BANK"                            : 0x480E,
    "TTD_STR_INDUSTRY_NAME_FOOD_PROCESSING_PLANT"           : 0x480F,
    "TTD_STR_INDUSTRY_NAME_PAPER_MILL"                      : 0x4810,
    "TTD_STR_INDUSTRY_NAME_GOLD_MINE"                       : 0x4811,
    "TTD_STR_INDUSTRY_NAME_BANK_TROPIC_ARCTIC"              : 0x4812,
    "TTD_STR_INDUSTRY_NAME_DIAMOND_MINE"                    : 0x4813,
    "TTD_STR_INDUSTRY_NAME_IRON_ORE_MINE"                   : 0x4814,
    "TTD_STR_INDUSTRY_NAME_FRUIT_PLANTATION"                : 0x4815,
    "TTD_STR_INDUSTRY_NAME_RUBBER_PLANTATION"               : 0x4816,
    "TTD_STR_INDUSTRY_NAME_WATER_SUPPLY"                    : 0x4817,
    "TTD_STR_INDUSTRY_NAME_WATER_TOWER"                     : 0x4818,
    "TTD_STR_INDUSTRY_NAME_FACTORY_2"                       : 0x4819,
    "TTD_STR_INDUSTRY_NAME_FARM_2"                          : 0x481A,
    "TTD_STR_INDUSTRY_NAME_LUMBER_MILL"                     : 0x481B,
    "TTD_STR_INDUSTRY_NAME_COTTON_CANDY_FOREST"             : 0x481C,
    "TTD_STR_INDUSTRY_NAME_CANDY_FACTORY"                   : 0x481D,
    "TTD_STR_INDUSTRY_NAME_BATTERY_FARM"                    : 0x481E,
    "TTD_STR_INDUSTRY_NAME_COLA_WELLS"                      : 0x481F,
    "TTD_STR_INDUSTRY_NAME_TOY_SHOP"                        : 0x4820,
    "TTD_STR_INDUSTRY_NAME_TOY_FACTORY"                     : 0x4821,
    "TTD_STR_INDUSTRY_NAME_PLASTIC_FOUNTAINS"               : 0x4822,
    "TTD_STR_INDUSTRY_NAME_FIZZY_DRINK_FACTORY"             : 0x4823,
    "TTD_STR_INDUSTRY_NAME_BUBBLE_GENERATOR"                : 0x4824,
    "TTD_STR_INDUSTRY_NAME_TOFFEE_QUARRY"                   : 0x4825,
    "TTD_STR_INDUSTRY_NAME_SUGAR_MINE"                      : 0x4826,
    "TTD_STR_NEWS_INDUSTRY_CONSTRUCTION"                    : 0x482D,
    "TTD_STR_NEWS_INDUSTRY_PLANTED"                         : 0x482E,
    "TTD_STR_NEWS_INDUSTRY_CLOSURE_GENERAL"                 : 0x4832,
    "TTD_STR_NEWS_INDUSTRY_CLOSURE_SUPPLY_PROBLEMS"         : 0x4833,
    "TTD_STR_NEWS_INDUSTRY_CLOSURE_LACK_OF_TREES"           : 0x4834,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_INCREASE_GENERAL"     : 0x4835,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_INCREASE_COAL"        : 0x4836,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_INCREASE_OIL"         : 0x4837,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_INCREASE_FARM"        : 0x4838,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_DECREASE_GENERAL"     : 0x4839,
    "TTD_STR_NEWS_INDUSTRY_PRODUCTION_DECREASE_FARM"        : 0x483A,
    "TTD_STR_ERROR_CAN_T_CONSTRUCT_THIS_INDUSTRY"           : 0x4830,
    "TTD_STR_ERROR_FOREST_CAN_ONLY_BE_PLANTED"              : 0x4831,
    "TTD_STR_ERROR_CAN_ONLY_BE_POSITIONED"                  : 0x483B,
}
# fmt: on


def signextend(param, info):
    # r = (x ^ m) - m; with m being (1 << (num_bits -1))
    m = expression.ConstantNumeric(1 << (info["size"] * 8 - 1))
    return nmlop.SUB(nmlop.XOR(param, m), m)


def global_param_write(info, expr, pos):
    if not ("writable" in info and info["writable"]):
        raise generic.ScriptError("Target parameter is not writable.", pos)
    return expression.Parameter(expression.ConstantNumeric(info["num"]), pos), expr


def global_param_read(info, pos):
    param = expression.Parameter(expression.ConstantNumeric(info["num"]), pos)
    if info["size"] == 1:
        mask = expression.ConstantNumeric(0xFF)
        param = nmlop.AND(param, mask)
    else:
        assert info["size"] == 4
    if "function" in info:
        return info["function"](param, info)
    return param


def param_from_info(name, info, pos):
    return expression.SpecialParameter(name, info, global_param_write, global_param_read, False, pos)


# fmt: off
global_parameters = {
    "climate":            {"num": 0x83, "size": 1},
    "loading_stage":      {"num": 0x84, "size": 4},
    "ttdpatch_version":   {"num": 0x8B, "size": 4},
    "current_palette":    {"num": 0x8D, "size": 1},
    "traininfo_y_offset": {"num": 0x8E, "size": 1, "writable": 1, "function": signextend},
    "game_mode":          {"num": 0x92, "size": 1},
    "ttd_platform":       {"num": 0x9D, "size": 4},
    "openttd_version":    {"num": 0xA1, "size": 4},
    "difficulty_level":   {"num": 0xA2, "size": 4},
    "date_loaded":        {"num": 0xA3, "size": 4},
    "year_loaded":        {"num": 0xA4, "size": 4},
}
# fmt: on


def misc_bit_write(info, expr, pos):
    param = expression.Parameter(expression.ConstantNumeric(info["param"], pos), pos)

    # param = (expr != 0) ? param | (1 << bit) : param & ~(1 << bit)
    expr = nmlop.CMP_NEQ(expr, 0, pos)
    or_expr = nmlop.OR(param, 1 << info["bit"], pos)
    and_expr = nmlop.AND(param, ~(1 << info["bit"]), pos)
    expr = expression.TernaryOp(expr, or_expr, and_expr, pos)
    return (param, expr)


def misc_bit_read(info, pos):
    return nmlop.HASBIT(expression.Parameter(expression.ConstantNumeric(info["param"], pos), pos), info["bit"])


def misc_grf_bit(name, info, pos):
    return expression.SpecialParameter(name, info, misc_bit_write, misc_bit_read, True, pos)


misc_grf_bits = {
    "traffic_side": {"param": 0x86, "bit": 4},
    "desert_paved_roads": {"param": 0x9E, "bit": 1},
    "train_width_32_px": {"param": 0x9E, "bit": 3},
    "second_rocky_tileset": {"param": 0x9E, "bit": 6},
}


def add_1920(expr, info):
    """
    Create a new expression that adds 1920 to a given expression.

    @param expr: The expression to add 1920 to.
    @type expr: L{Expression}

    @param info: Ignored.

    @return: A new expression that adds 1920 to the given expression.
    @rtype: L{Expression}
    """
    return nmlop.ADD(expr, 1920)


def map_exponentiate(expr, info):
    """
    Given a exponent, add an offset to it and compute the exponentiation with base 2.

    @param expr: The exponent.
    @type expr: L{Expression}

    @param info: Table with extra information, most notable 'log_offset', the value we need to
                 add to the given expression before computing the exponentiation.
    @type info: C{dict}

    @return: An expression computing 2**(expr + info['log_offset']).
    @rtype: L{Expression}
    """
    # map (log2(x) - a) to x, i.e. do 1 << (x + a)
    expr = nmlop.ADD(expr, info["log_offset"])
    return nmlop.SHIFT_LEFT(1, expr)


def patch_variable_read(info, pos):
    """
    Helper function to read special patch variables.

    @param info: Generic information about the parameter to read, like parameter number and size.
    @type info: C{dict}

    @param pos: Position information in the source file.
    @type pos: L{Position} or C{None}

    @return: An expression that reads the special variables.
    @rtype: L{Expression}
    """
    expr = expression.PatchVariable(info["num"], pos)
    if info["start"] != 0:
        expr = nmlop.SHIFT_RIGHT(expr, info["start"], pos)
    if info["size"] != 32:
        expr = nmlop.AND(expr, (1 << info["size"]) - 1, pos)
    if "function" in info:
        expr = info["function"](expr, info)
    return expr


def patch_variable(name, info, pos):
    return expression.SpecialParameter(name, info, None, patch_variable_read, False, pos)


# fmt: off
patch_variables = {
    "starting_year":           {"num": 0x0B, "start":  0, "size": 32, "function": add_1920},
    "freight_trains":          {"num": 0x0E, "start":  0, "size": 32},
    "plane_speed":             {"num": 0x10, "start":  0, "size": 32},
    "base_sprite_2cc":         {"num": 0x11, "start":  0, "size": 32},
    "map_type":                {"num": 0x13, "start": 24, "size":  2},
    "map_min_edge":            {"num": 0x13, "start": 20, "size":  4, "log_offset":  6, "function": map_exponentiate},
    "map_max_edge":            {"num": 0x13, "start": 16, "size":  4, "log_offset":  6, "function": map_exponentiate},
    "map_x_edge":              {"num": 0x13, "start": 12, "size":  4, "log_offset":  6, "function": map_exponentiate},
    "map_y_edge":              {"num": 0x13, "start":  8, "size":  4, "log_offset":  6, "function": map_exponentiate},
    "map_size":                {"num": 0x13, "start":  0, "size":  8, "log_offset": 12, "function": map_exponentiate},
    "max_height_level":        {"num": 0x14, "start":  0, "size": 32},
    "base_sprite_foundations": {"num": 0x15, "start":  0, "size": 32},
    "base_sprite_shores":      {"num": 0x16, "start":  0, "size": 32},
}
# fmt: on


def config_flag_read(bit, pos):
    return expression.SpecialCheck((0x01, r"\70"), 0x85, (0, 1), bit, "PatchFlag({})".format(bit), varsize=1, pos=pos)


def config_flag(name, info, pos):
    return expression.SpecialParameter(name, info, None, config_flag_read, True, pos)


# fmt: off
config_flags = {
    "long_bridges"            : 0x0F,
    "gradual_loading"         : 0x2C,
    "bridge_speed_limits"     : 0x34,
    "newtrains"               : 0x37,
    "newrvs"                  : 0x38,
    "newships"                : 0x39,
    "newplanes"               : 0x3A,
    "signals_on_traffic_side" : 0x3B,
    "electrified_railways"    : 0x3C,
    "newhouses"               : 0x59,
    "wagon_speed_limits"      : 0x5D,
    "newindustries"           : 0x67,
    "temperate_snowline"      : 0x6A,
    "newcargos"               : 0x6B,
    "dynamic_engines"         : 0x78,
    "variable_runningcosts"   : 0x7E,
    "256_persistent_registers": 0x80,
    "inflation"               : 0x81,
}
# fmt: on


def unified_maglev_read(info, pos):
    bit0 = nmlop.HASBIT(expression.Parameter(expression.ConstantNumeric(0x85), pos), 0x32)
    bit1 = nmlop.HASBIT(expression.Parameter(expression.ConstantNumeric(0x85), pos), 0x33)
    shifted_bit1 = nmlop.SHIFT_LEFT(bit1, 1)
    return nmlop.OR(shifted_bit1, bit0)


def unified_maglev(name, info, pos):
    return expression.SpecialParameter(name, info, None, unified_maglev_read, False, pos)


unified_maglev_var = {
    "unified_maglev": 0,
}


def setting_from_info(name, info, pos):
    return expression.SpecialParameter(name, info, global_param_write, global_param_read, False, pos)


def item_to_id(name, item, pos):
    if not isinstance(item.id, expression.ConstantNumeric):
        raise generic.ScriptError("Referencing item '{}' with a non-constant id is not possible.".format(name), pos)
    return expression.ConstantNumeric(item.id.value, pos)


def param_from_name(name, info, pos):
    del name  # unused; to match other id_list callbacks
    return expression.Parameter(expression.ConstantNumeric(info), pos)


def create_spritegroup_ref(name, info, pos):
    del name  # unused; to match other id_list callbacks
    return expression.SpriteGroupRef(expression.Identifier(info), [], pos)


cargo_numbers = {}

is_default_railtype_table = True
# if no railtype_table is provided, OpenTTD assumes these 4 railtypes
railtype_table = {"RAIL": 0, "ELRL": 1, "MONO": 1, "MGLV": 2}

is_default_roadtype_table = True
# if no roadtype_table is provided, OpenTTD sets all vehicles to ROAD
roadtype_table = {"ROAD": 0}

is_default_tramtype_table = True
# if no tramtype_table is provided, OpenTTD sets all vehicles to ELRL
tramtype_table = {"ELRL": 0}

identifier_refcount = {}
item_names = {}
settings = {}
named_parameters = {}
spritegroups = {"CB_FAILED": "CB_FAILED"}

const_list = [
    (constant_numbers, constant_number),
    (global_parameters, param_from_info),
    (misc_grf_bits, misc_grf_bit),
    (patch_variables, patch_variable),
    (named_parameters, param_from_name),
    cargo_numbers,
    railtype_table,
    roadtype_table,
    tramtype_table,
    (item_names, item_to_id),
    (settings, setting_from_info),
    (config_flags, config_flag),
    (unified_maglev_var, unified_maglev),
    (spritegroups, create_spritegroup_ref),
]


def print_stats():
    """
    Print statistics about used ids.
    """
    if len(cargo_numbers) > 0:
        # Ids FE and FF have special meanings in Action3, so we do not consider them valid ids.
        generic.print_info("Cargo translation table: {}/{}".format(len(cargo_numbers), 0xFE))
    if not is_default_railtype_table:
        generic.print_info("Railtype translation table: {}/{}".format(len(railtype_table), 0x100))
    if not is_default_roadtype_table:
        generic.print_info("Roadtype translation table: {}/{}".format(len(roadtype_table), 0x100))
    if not is_default_tramtype_table:
        generic.print_info("Tramtype translation table: {}/{}".format(len(tramtype_table), 0x100))
