const_table = {
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
    'LEVEL_CROSSING_CLOSED'     : 0,
    'LEVEL_CROSSING_OPEN'       : 1,
    'LEVEL_CROSSING_NONE'       : 1,

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
}
