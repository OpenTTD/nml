from nml import expression

constant_numbers = {
    #climates
    'CLIMATE_TEMPERATE'     : 0x00,
    'CLIMATE_ARCTIC'        : 0x01,
    'CLIMATE_TROPICAL'      : 0x02,
    'CLIMATE_TOYLAND'       : 0x03,

    'CLIMATE_NONE'          : 0x00,
    'CLIMATE_ALL'           : 0x0F,

    #never expire
    'VEHICLE_NEVER_EXPIRES' : 0xFF,

    #cargo classes
    'CC_NONE'         : 0x0000,
    'CC_PASSENGERS'   : 0x0001,
    'CC_MAIL'         : 0x0002,
    'CC_EXPRESS'      : 0x0004,
    'CC_ARMOURED'     : 0x0008,
    'CC_BULK'         : 0x0010,
    'CC_PIECE_GOODS'  : 0x0020,
    'CC_LIQUID'       : 0x0040,
    'CC_REFRIGERATED' : 0x0080,
    'CC_HAZARDOUS'    : 0x0100,
    'CC_COVERED'      : 0x0200,
    'CC_OVERSIZED'    : 0x0400,
    'CC_SPECIAL'      : 0x8000,
    'CC_ALL_NORMAL'   : 0x04FF,
    'CC_ALL'          : 0x84FF,

    #track type
    'TRACK_TYPE_RAIL'     : 0x00,
    'TRACK_TYPE_MONORAIL' : 0x01,
    'TRACK_TYPE_MAGLEV'   : 0x02,

    #engine class
    'ENGINE_CLASS_STEAM'    : 0x00,
    'ENGINE_CLASS_DIESEL'   : 0x08,
    'ENGINE_CLASS_ELECTRIC' : 0x28,
    'ENGINE_CLASS_MONORAIL' : 0x32,
    'ENGINE_CLASS_MAGLEV'   : 0x38,

    #running costs
    'RUNNING_COST_STEAM'    : 0x4C30,
    'RUNNING_COST_DIESEL'   : 0x4C36,
    'RUNNING_COST_ELECTRIC' : 0x4C3C,
    'RUNNING_COST_ROADVEH'  : 0x4C48,
    'RUNNING_COST_NONE'     : 0x0000,

    #vehicle cb flags
    'CBF_WAGON_POWER'       : 0x01,
    'CBF_WAGON_LENGTH'      : 0x02,
    'CBF_LOAD_AMOUNT'       : 0x04,
    'CBF_REFITTED_CAPACITY' : 0x08,
    'CBF_ARTICULATED_PARTS' : 0x10,
    'CBF_CARGO_SUFFIX'      : 0x20,
    'CBF_COLOR_MAPPING'     : 0x40,
    'CBF_SOUND_EFFECT'      : 0x80,

    #shorten factor
    'SHORTEN_TO_8_8' : 0x00,
    'SHORTEN_TO_7_8' : 0x01,
    'SHORTEN_TO_6_8' : 0x02,
    'SHORTEN_TO_5_8' : 0x03,
    'SHORTEN_TO_4_8' : 0x04,
    'SHORTEN_TO_3_8' : 0x05,
    'SHORTEN_TO_2_8' : 0x06,
    'SHORTEN_TO_1_8' : 0x07,

    #visual effect / wagon power
    'VISUAL_EFFECT_DEFAULT'  : 0x00,
    'VISUAL_EFFECT_STEAM'    : 0x10,
    'VISUAL_EFFECT_DIESEL'   : 0x20,
    'VISUAL_EFFECT_ELECTRIC' : 0x30,
    'VISUAL_EFFECT_DISABLE'  : 0x40,
    'DISABLE_WAGON_POWER'    : 0x80,

    #train misc flags
    'TRAIN_FLAG_TILT' : 0x01,
    'TRAIN_FLAG_2CC'  : 0x02,
    'TRAIN_FLAG_MU'   : 0x04,

    #roadveh misc flags
    'ROADVEH_FLAG_TRAM' : 0x01,
    'ROADVEH_FLAG_2CC'  : 0x02,

    #ship misc flags
    'SHIP_FLAG_2CC'  : 0x02,

    #aircrafts misc flags
    'AIRCRAFT_FLAG_2CC'  : 0x02,

    #for those, who can't tell the difference between a train and an aircraft:
    'VEHICLE_FLAG_2CC' : 0x02,

    #ai flags
    'AI_FLAG_PASSENGER' : 0x01,
    'AI_FLAG_CARGO'     : 0x00,

    #sound effects
    'SOUND_CARGO_SHIP'     : 0x04,
    'SOUND_PASSENGER_SHIP' : 0x05,
    'SOUND_PROPELLER_1'    : 0x06,
    'SOUND_JET_1'          : 0x07,
    'SOUND_BUS'            : 0x17,
    'SOUND_TRUCK_1'        : 0x18,
    'SOUND_TRUCK_2'        : 0x19,
    'SOUND_SUPERSONIC'     : 0x3B,
    'SOUND_JET_2'          : 0x3D,
    'SOUND_PROPELLER_2'    : 0x45,
    'SOUND_JET_3'          : 0x46,

    #sprite ids
    'SPRITE_ID_NEW_TRAIN'    : 0xFD,
    'SPRITE_ID_NEW_ROADVEH'  : 0xFF,
    'SPRITE_ID_NEW_SHIP'     : 0xFF,
    'SPRITE_ID_NEW_AIRCRAFT' : 0xFF,

    #aircraft type/size
    'AIRCRAFT_TYPE_NORMAL'     : 0x00,
    'AIRCRAFT_TYPE_HELICOPTER' : 0x02,
    'AIRCRAFT_SIZE_SMALL'      : 0x00,
    'AIRCRAFT_SIZE_LARGE'      : 0x01,

    #ground sprite IDs
    'GROUNDSPRITE_NORMAL'      : 3981,
    'GROUNDSPRITE_SNOW'        : 4550,
    'GROUNDSPRITE_DESERT'      : 4550,

    #railtype labels
    'RAILTYPE_RAIL'    : "RAIL",
    'RAILTYPE_ERAIL'   : "ELRL",
    'RAILTYPE_MONORAIL': "MONO",
    'RAILTYPE_MAGLEV'  : "MGLV",

    #railtype flags
    'RAILTYPE_FLAG_CATANERY' : 0x01,

    #type of default station graphics used for a railtype
    'RAILTYPE_STATION_NORMAL'   : 0,
    'RAILTYPE_STATION_MONORAIL' : 1,
    'RAILTYPE_STATION_MAGLEV'   : 2,

    #ground tile types as returned by railtypes varaction2 0x40
    'TILETYPE_NORMAL'           : 0x00,
    'TILETYPE_DESERT'           : 0x01,
    'TILETYPE_RAIN_FOREST'      : 0x02,
    'TILETYPE_SNOW'             : 0x04,

    #level crossing status as returned by railtypes varaction2 0x42
    'LEVEL_CROSSING_CLOSED'     : 1,
    'LEVEL_CROSSING_OPEN'       : 0,
    'LEVEL_CROSSING_NONE'       : 0,

    #acceleration model for trains
    'ACC_MODEL_RAIL'     : 0,
    'ACC_MODEL_MONORAIL' : 1,
    'ACC_MODEL_MAGLEV'   : 2,

    #default industry IDs
    'INDUSTRYTYPE_COAL_MINE'             : 0x00,
    'INDUSTRYTYPE_POWER_PLANT'           : 0x01,
    'INDUSTRYTYPE_SAWMILL'               : 0x02,
    'INDUSTRYTYPE_FOREST'                : 0x03,
    'INDUSTRYTYPE_OIL_REFINERY'          : 0x04,
    'INDUSTRYTYPE_OIL_RIG'               : 0x05,
    'INDUSTRYTYPE_TEMPERATE_FACTORY'     : 0x06,
    'INDUSTRYTYPE_PRINTING_WORKS'        : 0x07,
    'INDUSTRYTYPE_STEEL_MILL'            : 0x08,
    'INDUSTRYTYPE_TEMPERATE_ARCTIC_FARM' : 0x09,
    'INDUSTRYTYPE_COPPER_ORE_MINE'       : 0x0A,
    'INDUSTRYTYPE_OIL_WELLS'             : 0x0B,
    'INDUSTRYTYPE_TEMPERATE_BANK'         : 0x0C,
    'INDUSTRYTYPE_FOOD_PROCESSING_PLANT' : 0x0D,
    'INDUSTRYTYPE_PAPER_MILL'            : 0x0E,
    'INDUSTRYTYPE_GOLD_MINE'             : 0x0F,
    'INDUSTRYTYPE_TROPIC_ARCTIC_BANK'    : 0x10,
    'INDUSTRYTYPE_DIAMOND_MINE'          : 0x11,
    'INDUSTRYTYPE_IRON_ORE_MINE'         : 0x12,
    'INDUSTRYTYPE_FRUIT_PLANTATION'      : 0x13,
    'INDUSTRYTYPE_RUBBER_PLANTATION'     : 0x14,
    'INDUSTRYTYPE_WATER_WELL'            : 0x15,
    'INDUSTRYTYPE_WATER_TOWER'           : 0x16,
    'INDUSTRYTYPE_TROPIC_FACTORY'        : 0x17,
    'INDUSTRYTYPE_TROPIC_FARM'           : 0x18,
    'INDUSTRYTYPE_LUMBER_MILL'           : 0x19,
    'INDUSTRYTYPE_CANDYFLOSS_FOREST'     : 0x1A,
    'INDUSTRYTYPE_SWEETS_FACTORY'        : 0x1B,
    'INDUSTRYTYPE_BATTERY_FARM'          : 0x1C,
    'INDUSTRYTYPE_COLA_WELLS'            : 0x1D,
    'INDUSTRYTYPE_TOY_SHOP'              : 0x1E,
    'INDUSTRYTYPE_TOY_FACTORY'           : 0x1F,
    'INDUSTRYTYPE_PLASTIC_FOUNTAIN'      : 0x20,
    'INDUSTRYTYPE_FIZZY_DRINKS_FACTORY'  : 0x21,
    'INDUSTRYTYPE_BUBBLE_GENERATOR'      : 0x22,
    'INDUSTRYTYPE_TOFFE_QUARRY'          : 0x23,
    'INDUSTRYTYPE_SUGAR_MINE'            : 0x24,

    'INDUSTRYTYPE_UNKNOWN'               : 0xFE,
    'INDUSTRYTYPE_TOWN'                  : 0xFF,

    #industry production type flags (industry property 0x0B, prod_flags)
    'PRODUCTIONTYPE_EXACTIVE'            : 0x01,
    'PRODUCTIONTYPE_ORGANIC'             : 0x02,
    'PRODUCTIONTYPE_PROCESSING'          : 0x04,
    'PRODUCTIONTYPE_NONE'                : 0x00,

    #traffic side (right hand traffic when bit 4 is set)
    'TRAFFIC_SIDE_LEFT'                  : 0x00,
    'TRAFFIC_SIDE_RIGHT'                 : 0x10,

    #which platform has loaded this grf
    'PLATFORM_TTDPATCH'                  : 0x00,
    'PLATFORM_OPENTTD'                   : 0x01,

    #ttdpatch flags
    'CONFIGFLAG_KEEPSMALLAIRPORT'           : 0x0C,
    'CONFIGFLAG_NEWAIRPORTS'                : 0x0D,
    'CONFIGFLAG_LARGESTATIONS'              : 0x0E,
    'CONFIGFLAG_LONGBRIDGES'                : 0x0F,
    'CONFIGFLAG_LOADTIME'                   : 0x10,
    'CONFIGFLAG_PRESIGNALS'                 : 0x12,
    'CONFIGFLAG_EXTPRESIGNALS'              : 0x13,
    'CONFIGFLAG_PERSISTANT_ENGINES'         : 0x16,
    'CONFIGFLAG_MULTIHEAD'                  : 0x1B,
    'CONFIGFLAG_LOW_MEMORY'                 : 0x1D,
    'CONFIGFLAG_GENERAL_FIXES'              : 0x1E,
    'CONFIGFLAG_MORE_AIRPORTS'              : 0x27,
    'CONFIGFLAG_MAMMOTH_TRAINS'             : 0x28,
    'CONFIGFLAG_TRAIN_REFIT'                : 0x29,
    'CONFIGFLAG_SUBSIDIARIES'               : 0x2B,
    'CONFIGFLAG_GRADUAL_LOADING'            : 0x2C,
    'CONFIGFLAG_NOT_UNIFIED_MAGLEV'         : 0x32,
    'CONFIGFLAG_UNIFIED_MAGLEV'             : 0x33,
    'CONFIGFLAG_BRIDGE_SPEEDLIMITS'         : 0x34,
    'CONFIGFLAG_ETERNAL_GAME'               : 0x36,
    'CONFIGFLAG_NEW_TRAINS'                 : 0x37,
    'CONFIGFLAG_NEW_ROAD_VEHICLES'          : 0x38,
    'CONFIGFLAG_NEW_SHIPS'                  : 0x39,
    'CONFIGFLAG_NEW_AIRCRAFT'               : 0x3A,
    'CONFIGFLAG_SIGNALS_ON_TRAFFIC_SIDE'    : 0x3B,
    'CONFIGFLAG_ELECTRIFIED_RAILWAY'        : 0x3C,
    'CONFIGFLAG_LOAD_ALL_GRAPHICS'          : 0x41,
    'CONFIGFLAG_SEMAPHORES'                 : 0x43,
    'CONFIGFLAG_ENHANCE_GUI'                : 0x4B,
    'CONFIGFLAG_NEW_AGE_RATING'             : 0x4C,
    'CONFIGFLAG_BUILD_ON_SLOPES'            : 0x4D,
    'CONFIGFLAG_FULL_LOAD_ANY'              : 0x4E,
    'CONFIGFLAG_PLANE_SPEED_FACTOR'         : 0x4F,
    'CONFIGFLAG_MORE_INDUSTRY_PER_CLIMATE'  : 0x50,
    'CONFIGFLAG_TOYLAND_FEATURES'           : 0x51,
    'CONFIGFLAG_NEWSTATIONS'                : 0x52,
    'CONFIGFLAG_TRACKTYPE_COST_DIFF'        : 0x53,
    'CONFIGFLAG_MANUAL_CONVERT'             : 0x54,
    'CONFIGFLAG_BUILD_ON_COASTS'            : 0x55,
    'CONFIGFLAG_CANALS'                     : 0x56,
    'CONFIGFLAG_NEW_START_YEAR'             : 0x57,
    'CONFIGFLAG_FREIGHT_TRAINS'             : 0x58,
    'CONFIGFLAG_NEW_HOUSES'                 : 0x59,
    'CONFIGFLAG_NEW_BRIDGES'                : 0x5A,
    'CONFIGFLAG_NEW_TOWNNAMES'              : 0x5B,
    'CONFIGFLAG_MORE_ANIMATION'             : 0x5C,
    'CONFIGFLAG_WAGON_SPEED_LIMITS'         : 0x5D,
    'CONFIGFLAG_NEWS_HISTORY'               : 0x5E,
    'CONFIGFLAG_CUSTOM_BRIDGE_HEADS'        : 0x5F,
    'CONFIGFLAG_NEW_CARGO_DISTRIBUTION'     : 0x60,
    'CONFIGFLAG_WINDOW_SNAP'                : 0x61,
    'CONFIGFLAG_TOWNS_BUILD_NO_ROADS'       : 0x62,
    'CONFIGFLAG_PATH_BASED_SIGNALING'       : 0x63,
    'CONFIGFLAG_AI_CHOOSE_CHANCES'          : 0x64,
    'CONFIGFLAG_RESOLUTION_WIDTH'           : 0x65,
    'CONFIGFLAG_RESOLUTION_HEIGHT'          : 0x66,
    'CONFIGFLAG_NEW_INDUSTRIES'             : 0x67,
    'CONFIGFLAG_FIFO_LOADING'               : 0x68,
    'CONFIGFLAG_TOWN_ROAD_BRANCH_PROB'      : 0x69,
    'CONFIGFLAG_TEMPERATE_SNOWLINE'         : 0x6A,
    'CONFIGFLAG_NEW_CARGOS'                 : 0x6B,
    'CONFIGFLAG_ENHANCED_MULTIPLAYER'       : 0x6C,
    'CONFIGFLAG_ONEWAY_ROADS'               : 0x6D,
    'CONFIGFLAG_IRREGULAR_STATIONS'         : 0x6E,
    'CONFIGFLAG_MORE_STATISTICS'            : 0x6F,
    'CONFIGFLAG_NEW_SOUNDS'                 : 0x70,
    'CONFIGFLAG_AUTOREPLACE'                : 0x71,
    'CONFIGFLAG_AUTOSLOPE'                  : 0x72,
    'CONFIGFLAG_FOLLOW_VEHICLE'             : 0x73,
    'CONFIGFLAG_TRAMS'                      : 0x74,
    'CONFIGFLAG_ENHANCED_TUNNELS'           : 0x75,
    'CONFIGFLAG_SHORT_ROAD_VEHICLES'        : 0x76,
    'CONFIGFLAG_ARTICULATED_ROAD_VEHICLES'  : 0x77,
    'CONFIGFLAG_ENGINE_POOL'                : 0x78,
    'CONFIGFLAG_VARIABLE_RUNNING_COSTS'     : 0x7E,
    'CONFIGFLAG_ANY'                        : 0x7F,
}

def param_from_num(num, pos):
    return expression.Parameter(expression.ConstantNumeric(num), pos)

global_parameters = {
    'climate'                            : 0x83,
    'ttdpatch_flags'                     : 0x85,
    'traffic_side'                       : 0x86,
    'ttdpatch_version'                   : 0x8B,
    'ttd_version'                        : 0x8D,
    'ttd_platform'                       : 0x9D,
    'openttd_version'                    : 0xA1,
    'date_loaded'                        : 0xA3,
    'year_loaded'                        : 0xA4,
}

cargo_numbers = {}
railtype_table = {}

const_list = [constant_numbers, (global_parameters, param_from_num), cargo_numbers, railtype_table]
