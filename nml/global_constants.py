from nml import expression, generic, nmlop

constant_numbers = {
    #climates
    'CLIMATE_TEMPERATE'     : 0x00,
    'CLIMATE_ARCTIC'        : 0x01,
    'CLIMATE_TROPIC'        : 0x02,
    'CLIMATE_TROPICAL'      : 0x02,
    'CLIMATE_TOYLAND'       : 0x03,
    'CLIMATE_SNOW'          : 0x0B, # Only for house property available_mask

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
    'VEH_CBF_WAGON_POWER'       : 0x01,
    'VEH_CBF_WAGON_LENGTH'      : 0x02,
    'VEH_CBF_LOAD_AMOUNT'       : 0x04,
    'VEH_CBF_REFITTED_CAPACITY' : 0x08,
    'VEH_CBF_ARTICULATED_PARTS' : 0x10,
    'VEH_CBF_CARGO_SUFFIX'      : 0x20,
    'VEH_CBF_COLOR_MAPPING'     : 0x40,
    'VEH_CBF_SOUND_EFFECT'      : 0x80,

    #corresponding callbacks
    'VEH_CB_WAGON_POWER'            : 0x10,
    'VEH_CB_WAGON_LENGTH'           : 0x11,
    'VEH_CB_LOAD_AMOUNT'            : 0x12,
    'VEH_CB_REFITTED_CAPACITY'      : 0x15,
    'VEH_CB_ARTICULATED_PARTS'      : 0x16,
    'VEH_CB_CARGO_SUFFIX'           : 0x19,
    'VEH_CB_CAN_ATTACH_WAGON'       : 0x1D,
    'VEH_CB_TEXT_PURCHASE_SCREEN'   : 0x23,
    'VEH_CB_COLOUR_MAPPING'         : 0x2D,
    'VEH_CB_START_STOP_CHECK'       : 0x31,
    'VEH_CB_32DAY'                  : 0x32,
    'VEH_CB_SOUND_EFFECT'           : 0x33,
    'VEH_CB_AUTOREPLACE_SELECT'     : 0x34,
    'VEH_CB_VEHICLE_PROPERTIES'     : 0x36,

    #properties for callback 0x36
    'PROP_TRAINS_LOADING_SPEED'                 : 0x07,
    'PROP_TRAINS_SPEED'                         : 0x09,
    'PROP_TRAINS_POWER'                         : 0x0B,
    'PROP_TRAINS_RUNNING_COST_FACTOR'           : 0x0D,
    'PROP_TRAINS_CARGO_CAPACITY'                : 0x14,
    'PROP_TRAINS_WEIGHT'                        : 0x16,
    'PROP_TRAINS_COST_FACTOR'                   : 0x17,
    'PROP_TRAINS_TRACTIVE_EFFORT_COEFFICIENT'   : 0x1F,
    'PROP_TRAINS_SHORTEN_VEHICLE'               : 0x21,
    'PROP_TRAINS_VISUAL_EFFECT'                 : 0x22,
    'PROP_TRAINS_BITMASK_VEHICLE_INFO'          : 0x25,

    'PROP_ROADVEHS_LOADING_SPEED'               : 0x07,
    'PROP_ROADVEHS_RUNNING_COST_FACTOR'         : 0x09,
    'PROP_ROADVEHS_CARGO_CAPACITY'              : 0x0F,
    'PROP_ROADVEHS_COST_FACTOR'                 : 0x11,

    'PROP_SHIPS_LOADING_SPEED'                  : 0x07,
    'PROP_SHIPS_COST_FACTOR'                    : 0x0A,
    'PROP_SHIPS_SPEED'                          : 0x0B,
    'PROP_SHIPS_CARGO_CAPACITY'                 : 0x0D,
    'PROP_SHIPS_RUNNING_COST_FACTOR'            : 0x0F,

    'PROP_AIRCRAFT_LOADING_SPEED'               : 0x07,
    'PROP_AIRCRAFT_COST_FACTOR'                 : 0x0B,
    'PROP_AIRCRAFT_SPEED'                       : 0x0C,
    'PROP_AIRCRAFT_RUNNING_COST_FACTOR'         : 0x0E,
    'PROP_AIRCRAFT_PASSENGER_CAPACITY'          : 0x0F,
    'PROP_AIRCRAFT_MAIL_CAPACITY'               : 0x11,

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
    'SOUND_SPLAT'                          : 0x00,
    'SOUND_FACTORY_WHISTLE'                : 0x01,
    'SOUND_TRAIN'                          : 0x02,
    'SOUND_TRAIN_THROUGH_TUNNEL'           : 0x03,
    'SOUND_SHIP_HORN'                      : 0x04,
    'SOUND_FERRY_HORN'                     : 0x05,
    'SOUND_PLANE_TAKE_OFF'                 : 0x06,
    'SOUND_JET'                            : 0x07,
    'SOUND_TRAIN_HORN'                     : 0x08,
    'SOUND_MINING_MACHINERY'               : 0x09,
    'SOUND_ELECTRIC_SPARK'                 : 0x0A,
    'SOUND_STEAM'                          : 0x0B,
    'SOUND_LEVEL_CROSSING'                 : 0x0C,
    'SOUND_VEHICLE_BREAKDOWN'              : 0x0D,
    'SOUND_TRAIN_BREAKDOWN'                : 0x0E,
    'SOUND_CRASH'                          : 0x0F,
    'SOUND_EXPLOSION'                      : 0x10,
    'SOUND_BIG_CRASH'                      : 0x11,
    'SOUND_CASHTILL'                       : 0x12,
    'SOUND_BEEP'                           : 0x13,
    'SOUND_MORSE'                          : 0x14,
    'SOUND_SKID_PLANE'                     : 0x15,
    'SOUND_HELICOPTER'                     : 0x16,
    'SOUND_BUS_START_PULL_AWAY'            : 0x17,
    'SOUND_BUS_START_PULL_AWAY_WITH_HORN'  : 0x18,
    'SOUND_TRUCK_START'                    : 0x19,
    'SOUND_TRUCK_START_2'                  : 0x1A,
    'SOUND_APPLAUSE'                       : 0x1B,
    'SOUND_OOOOH'                          : 0x1C,
    'SOUND_SPLAT'                          : 0x1D,
    'SOUND_SPLAT_2'                        : 0x1E,
    'SOUND_JACKHAMMER'                     : 0x1F,
    'SOUND_CAR_HORN'                       : 0x20,
    'SOUND_CAR_HORN_2'                     : 0x21,
    'SOUND_SHEEP'                          : 0x22,
    'SOUND_COW'                            : 0x23,
    'SOUND_HORSE'                          : 0x24,
    'SOUND_BLACKSMITH_ANVIL'               : 0x25,
    'SOUND_SAWMILL'                        : 0x26,
    'SOUND_GOOD_YEAR'                      : 0x27,
    'SOUND_BAD_YEAR'                       : 0x28,
    'SOUND_RIP'                            : 0x29,
    'SOUND_EXTRACT_AND_POP'                : 0x2A,
    'SOUND_COMEDY_HIT'                     : 0x2B,
    'SOUND_MACHINERY'                      : 0x2C,
    'SOUND_RIP_2'                          : 0x2D,
    'SOUND_EXTRACT_AND_POP'                : 0x2E,
    'SOUND_POP'                            : 0x2F,
    'SOUND_CARTOON_SOUND'                  : 0x30,
    'SOUND_EXTRACT'                        : 0x31,
    'SOUND_POP_2'                          : 0x32,
    'SOUND_PLASTIC_MINE'                   : 0x33,
    'SOUND_WIND'                           : 0x34,
    'SOUND_COMEDY_BREAKDOWN'               : 0x35,
    'SOUND_CARTOON_CRASH'                  : 0x36,
    'SOUND_BALLOON_SQUEAK'                 : 0x37,
    'SOUND_CHAINSAW'                       : 0x38,
    'SOUND_HEAVY_WIND'                     : 0x39,
    'SOUND_COMEDY_BREAKDOWN_2'             : 0x3A,
    'SOUND_JET_OVERHEAD'                   : 0x3B,
    'SOUND_COMEDY_CAR'                     : 0x3C,
    'SOUND_ANOTHER_JET_OVERHEAD'           : 0x3D,
    'SOUND_COMEDY_CAR_2'                   : 0x3E,
    'SOUND_COMEDY_CAR_3'                   : 0x3F,
    'SOUND_COMEDY_CAR_START_AND_PULL_AWAY' : 0x40,
    'SOUND_MAGLEV'                         : 0x41,
    'SOUND_LOON_BIRD'                      : 0x42,
    'SOUND_LION'                           : 0x43,
    'SOUND_MONKEYS'                        : 0x44,
    'SOUND_PLANE_CRASHING'                 : 0x45,
    'SOUND_PLANE_ENGINE_SPUTTERING'        : 0x46,
    'SOUND_MAGLEV_2'                       : 0x47,
    'SOUND_DISTANT_BIRD'                   : 0x48,

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
    
    #house callback flags
    'HOUSE_CBF_BUILD'               : 0x01,
    'HOUSE_CBF_ANIM_NEXT_FRAME'     : 0x02,
    'HOUSE_CBF_ANIM_STARTSTOP'      : 0x04,
    'HOUSE_CBF_CONSTRUCTION_ANIM'   : 0x08,
    'HOUSE_CBF_COLOUR'              : 0x10,
    'HOUSE_CBF_CARGO_AMOUNT_ACCEPT' : 0x20,
    'HOUSE_CBF_ANIM_FRAME_LENGTH'   : 0x40,
    'HOUSE_CBF_DESTRUCTION'         : 0x80,
    'HOUSE_CBF_CARGO_TYPE_ACCEPT'   : 0x100,
    'HOUSE_CBF_CARGO_PRODUCTION'    : 0x200,
    'HOUSE_CBF_PROTECTION'          : 0x400,
    'HOUSE_CBF_FOUNDATIONS'         : 0x800,
    'HOUSE_CBF_AUTOSLOPE'           : 0x1000,

    #corresponding callbacks
    'HOUSE_CB_BUILD'                : 0x17,
    'HOUSE_CB_ANIM_NEXT_FRAME'      : 0x1A,
    'HOUSE_CB_ANIM_STARTSTOP'       : 0x1B,
    'HOUSE_CB_CONSTRUCTION_ANIM'    : 0x1C,
    'HOUSE_CB_COLOUR'               : 0x1E,
    'HOUSE_CB_CARGO_AMOUNT_ACCEPT'  : 0x1F,
    'HOUSE_CB_ANIM_FRAME_LENGTH'    : 0x20,
    'HOUSE_CB_DESTRUCTION'          : 0x21,
    'HOUSE_CB_CARGO_TYPE_ACCEPT'    : 0x2A,
    'HOUSE_CB_CARGO_PRODUCTION'     : 0x2E,
    'HOUSE_CB_PROTECTION'           : 0x143,
    'HOUSE_CB_ACCEPTED_CARGO'       : 0x148,
    'HOUSE_CB_BUILDING_NAME'        : 0x14D,
    'HOUSE_CB_FOUNDATIONS'          : 0x14E,
    'HOUSE_CB_AUTOSLOPE'            : 0x14F,

    #house flags
    'HOUSE_FLAG_SIZE_1x1'           : 0x01,
    'HOUSE_FLAG_NOT_SLOPED'         : 0x02,
    'HOUSE_FLAG_SIZE_2x1'           : 0x04,
    'HOUSE_FLAG_SIZE_1x2'           : 0x08,
    'HOUSE_FLAG_SIZE_2x2'           : 0x10,
    'HOUSE_FLAG_ANIMATE'            : 0x20,
    'HOUSE_FLAG_CHURCH'             : 0x40,
    'HOUSE_FLAG_STADIUM'            : 0x80,
    'HOUSE_FLAG_ONLY_SE'            : 0x0100,
    'HOUSE_FLAG_PROTECTED'          : 0x0200,
    'HOUSE_FLAG_SYNC_CALLBACK'      : 0x0400,
    'HOUSE_FLAG_RANDOM_ANIMATION'   : 0x0800,

    #cargo acceptance
    'HOUSE_ACCEPT_GOODS'            : 0x00,
    'HOUSE_ACCEPT_FOOD'             : 0x10, # 0x80 / 8
    'HOUSE_ACCEPT_FIZZY_DRINKS'     : 0x10, # 0x80 / 8
    
    #town zones
    'TOWNZONE_EDGE'                 : 0x00,
    'TOWNZONE_OUTSKIRT'             : 0x01,
    'TOWNZONE_OUTER_SUBURB'         : 0x02,
    'TOWNZONE_INNER_SUBURB'         : 0x03,
    'TOWNZONE_CENTRE'               : 0x04,

    #industry callback flags
    'IND_CBF_AVAILABILITY'          : 0x0001,
    'IND_CBF_PROD_CB_CARGO_ARRIVE'  : 0x0002,
    'IND_CBF_PROD_CB_256_TICKS'     : 0x0004,
    'IND_CBF_LOCATION_CHECK'        : 0x0008,
    'IND_CBF_RANDOM_PROD_CHANGE'    : 0x0010,
    'IND_CBF_MONTLY_PROD_CHANGE'    : 0x0020,
    'IND_CBF_CARGO_SUBTYPE_DISPLAY' : 0x0040,
    'IND_CBF_EXTRA_TEXT_FUND'       : 0x0080,
    'IND_CBF_EXTRA_TEXT_INDUSTRY'   : 0x0100,
    'IND_CBF_CONTROL_SPECIAL'       : 0x0200,
    'IND_CBF_STOP_ACCEPT_CARGO'     : 0x0400,
    'IND_CBF_COLOR'                 : 0x0800,
    'IND_CBF_CARGO_INPUT'           : 0x1000,
    'IND_CBF_CARGO_OUTPUT'          : 0x2000,

    #corresponding callbacks
    'IND_CB_AVAILABILITY'           : 0x22,
    'IND_CB_LOCATION_CHECK'         : 0x28,
    'IND_CB_RANDOM_PROD_CHANGE'     : 0x29,
    'IND_CB_MONTLY_PROD_CHANGE'     : 0x35,
    'IND_CB_CARGO_SUBTYPE_DISPLAY'  : 0x37,
    'IND_CB_EXTRA_TEXT_FUND'        : 0x38,
    'IND_CB_EXTRA_TEXT_INDUSTRY'    : 0x3A,
    'IND_CB_CONTROL_SPECIAL'        : 0x3B,
    'IND_CB_STOP_ACCEPT_CARGO'      : 0x3D,
    'IND_CB_COLOR'                  : 0x14A,
    'IND_CB_CARGO_INPUT'            : 0x14B,
    'IND_CB_CARGO_OUTPUT'           : 0x14C,

    #object labels
    'OBJ_TRANSMITTER'          : "TRNS",
    'OBJ_LIGHTHOUSE'           : "LTHS",

    #object flags
    'OBJ_FLAG_ONLY_SE'         : 0x01,
    'OBJ_FLAG_IRREMOVABLE'     : 0x02,
    'OBJ_FLAG_ANYTHING_REMOVE' : 0x04,
    'OBJ_FLAG_ON_WATER'        : 0x08,
    'OBJ_FLAG_REMOVE_IS_INCOME': 0x10,
    'OBJ_FLAG_NO_FOUNDATIONS'  : 0x20,
    'OBJ_FLAG_ANIMATED'        : 0x40,
    'OBJ_FLAG_ONLY_INGAME'     : 0x80,
    'OBJ_FLAG_2CC'             : 0x100,
    'OBJ_FLAG_NOT_ON_LAND'     : 0x200,
    'OBJ_FLAG_DRAW_WATER'      : 0x400,
    'OBJ_FLAG_ALLOW_BRIDGE'    : 0x800,
    'OBJ_FLAG_RANDOM_ANIMATION': 0x1000,

    #object animation triggers
    'OBJ_ANIM_IS_BUILT'        : 0x01,
    'OBJ_ANIM_PERIODIC'        : 0x02,
    'OBJ_ANIM_SYNC'            : 0x04,

    #object callback flags
    'OBJ_CBF_SLOPE_CHECK'      : 0x01,
    'OBJ_CBF_DECIDE_ANIM'      : 0x02,
    'OBJ_CBF_DECIDE_ANIM_SPEED': 0x04,
    'OBJ_CBF_DECIDE_COLOUR'    : 0x08,
    'OBJ_CBF_ADDITIONAL_TEXT'  : 0x10,
    'OBJ_CBF_AUTOSLOPE'        : 0x20,

    #corresponding callbacks
    'OBJ_CB_SLOPE_CHECK'            : 0x157,
    'OBJ_CB_DECIDE_ANIM'            : 0x158,
    'OBJ_CB_DECIDE_ANIM_SPEED'      : 0x159,
    'OBJ_CB_DECIDE_ANIM_LENGTH'     : 0x15A,
    'OBJ_CB_DECIDE_COLOUR'          : 0x15B,
    'OBJ_CB_ADDITIONAL_TEXT'        : 0x15C,
    'OBJ_CB_AUTOSLOPE'              : 0x15D,

    #airport tile callback flags
    'APT_CBF_DECIDE_ANIM'       : 0x01,
    'APT_CBF_DECIDE_ANIM_SPEED' : 0x02,
    'APT_CBF_SLOPE_CHECK'       : 0x10,
    'APT_CBF_FOUNDATIONS'       : 0x20,
    'APT_CBF_AUTOSLOPE'         : 0x40,

    #corresponding callbacks
    'APT_CB_DECIDE_ANIM'        : 0x153,
    'APT_CB_DECIDE_ANIM_SPEED'  : 0x154,
    'APT_CB_FOUNDATIONS'        : 0x150,

    #railtype flags
    'RAILTYPE_FLAG_CATANERY'          : 0x01,
    'RAILTYPE_FLAG_NO_LEVEL_CROSSING' : 0x02, # for OpenTTD > r20049

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
    'INDUSTRYTYPE_TEMPERATE_BANK'        : 0x0C,
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
    'PRODUCTIONTYPE_EXTRACTIVE'          : 0x01,
    'PRODUCTIONTYPE_ORGANIC'             : 0x02,
    'PRODUCTIONTYPE_PROCESSING'          : 0x04,
    'PRODUCTIONTYPE_NONE'                : 0x00,

    #traffic side (right hand traffic when bit 4 is set)
    'TRAFFIC_SIDE_LEFT'                  : 0x00,
    'TRAFFIC_SIDE_RIGHT'                 : 0x10,

    #which platform has loaded this grf
    'PLATFORM_TTDPATCH'                  : 0x00,
    'PLATFORM_OPENTTD'                   : 0x01,

    #player types (vehicle var 0x43)
    'PLAYERTYPE_HUMAN'                   : 0,
    'PLAYERTYPE_AI'                      : 1,
    'PLAYERTYPE_HUMAN_IN_AI'             : 2,
    'PLAYERTYPE_AI_IN_HUMAN'             : 3,

    #airport types (vehicle var 0x44)
    'AIRPORTTYPE_SMALL'                  : 0,
    'AIRPORTTYPE_LARGE'                  : 1,
    'AIRPORTTYPE_HELIPORT'               : 2,
    'AIRPORTTYPE_OILRIG'                 : 3,

    #Direction for e.g. airport layouts, vehicle direction
    'DIRECTION_NORTH'                     : 0,
    'DIRECTION_NORTHEAST'                 : 1,
    'DIRECTION_EAST'                      : 2,
    'DIRECTION_SOUTHEAST'                 : 3,
    'DIRECTION_SOUTH'                     : 4,
    'DIRECTION_SOUTHWEST'                 : 5,
    'DIRECTION_WEST'                      : 6,
    'DIRECTION_NORTHWEST'                 : 7,

    #loading stages
    'LOADINGSTAGE_INITIALIZE'             : 0x0000,
    'LOADINGSTAGE_RESERVE'                : 0x0101,
    'LOADINGSTAGE_ACTIVATE'               : 0x0201,
    'LOADINGSTAGE_TEST'                   : 0x0401,

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
    
    #palettes
    'PALETTE_DOS'                           : 0,
    'PALETTE_WIN'                           : 1,

    #game mode
    'GAMEMODE_MENU'                         : 0,
    'GAMEMODE_GMAE'                         : 1,
    'GAMEMODE_EDITOR'                       : 2,

    #difficulty
    'DIFFICULTY_EASY'                       : 0,
    'DIFFICULTY_MEDIUM'                     : 1,
    'DIFFICULTY_HARD'                       : 2,
    'DIFFICULTY_CUSTOM'                     : 3,

    #display options
    'DISPLAY_TOWN_NAMES'                    : 0,
    'DISPLAY_STATION_NAMES'                 : 1,
    'DISPLAY_SIGNS'                         : 2,
    'DISPLAY_ANIMATION'                     : 3,
    'DISPLAY_FULL_DETAIL'                   : 5,

    #map types (ttdp variable 0x13)
    'MAP_TYPE_X_BIGGER'                     : 0, #bit 0 and 1 clear
    'MAP_TYPE_RECTANGULAR'                  : 1, #bit 0 set
    'MAP_TYPE_Y_BIGGER'                     : 2, #bit 0 clear, bit 1 set

    #Random triggers
    'TRIGGER_ALL'                           : 0x80,

    'TRIGGER_VEHICLE_NEW_LOAD'              : 0x01,
    'TRIGGER_VEHICLE_SERVICE'               : 0x02,
    'TRIGGER_VEHICLE_UNLOAD_ALL'            : 0x04,
    'TRIGGER_VEHICLE_ANY_LOAD'              : 0x08,
    'TRIGGER_VEHICLE_32_CALLBACK'           : 0x10,

    'TRIGGER_STATION_NEW_CARGO'             : 0x01,
    'TRIGGER_STATION_NO_MORE_CARGO'         : 0x02,
    'TRIGGER_STATION_TRAIN_ARRIVES'         : 0x04,
    'TRIGGER_STATION_TRAIN_LEAVES'          : 0x08,
    'TRIGGER_STATION_TRAIN_LOADS_UNLOADS'   : 0x10,
    'TRIGGER_STATION_TRAIN_RESERVES'        : 0x20,

    'TRIGGER_HOUSE_TILELOOP'                : 0x01,
    'TRIGGER_HOUSE_TOP_TILELOOP'            : 0x02,

    'TRIGGER_INDUSTRYTILE_TILELOOP'         : 0x01,
    'TRIGGER_INDUSTRYTILE_256_TICKS'        : 0x02,
    'TRIGGER_INDUSTRYTILE_CARGO_DELIVERY'   : 0x04,

    #Tile classes
    'TILE_CLASS_GROUND'                     : 0x00,
    'TILE_CLASS_RAIL'                       : 0x01,
    'TILE_CLASS_ROAD'                       : 0x02,
    'TILE_CLASS_HOUSE'                      : 0x03,
    'TILE_CLASS_TREES'                      : 0x04,
    'TILE_CLASS_STATION'                    : 0x05,
    'TILE_CLASS_WATER'                      : 0x06,
    'TILE_CLASS_INDUSTRY'                   : 0x08,
    'TILE_CLASS_TUNNEL_BRIDGE'              : 0x09,
    'TILE_CLASS_OBJECTS'                    : 0x0A,
}

def signextend(param, info):
    #r = (x ^ m) - m; with m being (1 << (num_bits -1))
    m = expression.ConstantNumeric(1 << (info['size'] * 8 - 1))
    return expression.BinOp(nmlop.SUB, expression.BinOp(nmlop.XOR, param, m, param.pos), m, param.pos)

def global_param_write(info, expr, pos):
    if not ('writable' in info and info['writable']): raise generic.ScriptError("Target parameter is not writable.", pos)
    return expression.Parameter(expression.ConstantNumeric(info['num']), pos), expr

def global_param_read(info, pos):
    param = expression.Parameter(expression.ConstantNumeric(info['num']), pos)
    if info['size'] == 1:
        mask = expression.ConstantNumeric(0xFF)
        param = expression.BinOp(nmlop.AND, param, mask)
    else:
        assert info['size'] == 4
    if 'function' in info: return info['function'](param, info)
    return param

def param_from_info(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(global_parameters, info), info, global_param_write, global_param_read, False, pos)

global_parameters = {
    'climate'                            : {'num': 0x83, 'size': 1},
    'loading_stage'                      : {'num': 0x84, 'size': 4},
    'ttdpatch_flags'                     : {'num': 0x85, 'size': 4},
    'traffic_side'                       : {'num': 0x86, 'size': 1},
    'ttdpatch_version'                   : {'num': 0x8B, 'size': 4},
    'current_palette'                    : {'num': 0x8D, 'size': 1},
    'traininfo_y_offset'                 : {'num': 0x8E, 'size': 1, 'writable': 1, 'function': signextend},
    'game_mode'                          : {'num': 0x82, 'size': 1},
    'ttd_platform'                       : {'num': 0x9D, 'size': 4},
    'openttd_version'                    : {'num': 0xA1, 'size': 4},
    'difficulty_level'                   : {'num': 0xA2, 'size': 4},
    'date_loaded'                        : {'num': 0xA3, 'size': 4},
    'year_loaded'                        : {'num': 0xA4, 'size': 4},
}

def misc_bit_write(info, expr, pos):
    param = expression.Parameter(expression.ConstantNumeric(info['param'], pos), pos)

    #param = (expr != 0) ? param | (1 << bit) : param & ~(1 << bit)
    expr = expression.BinOp(nmlop.CMP_NEQ, expr, expression.ConstantNumeric(0, pos), pos)
    or_expr = expression.BinOp(nmlop.OR, param, expression.ConstantNumeric(1 << info['bit'], pos), pos)
    and_expr = expression.BinOp(nmlop.AND, param, expression.ConstantNumeric(~(1 << info['bit']), pos), pos)
    expr = expression.TernaryOp(expr, or_expr, and_expr, pos)
    return (param, expr)

def misc_bit_read(info, pos):
    return expression.BinOp(nmlop.HASBIT, expression.Parameter(expression.ConstantNumeric(info['param'], pos), pos), expression.ConstantNumeric(info['bit'], pos), pos)

def misc_grf_bit(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(misc_grf_bits, info), info, misc_bit_write, misc_bit_read, True, pos)

misc_grf_bits = {
    'desert_paved_roads'                 : {'param': 0x9E, 'bit': 1},
    'train_width_32_px'                  : {'param': 0x9E, 'bit': 3},
}

def add_1920(param, info):
    return expression.BinOp(nmlop.ADD, param, expression.ConstantNumeric(1920, param.pos), param.pos)

def map_exponentiate(param, info):
    #map (log2(x) - a) to x, i.e. do 1 << (x + a)
    param = expression.BinOp(nmlop.ADD, param, expression.ConstantNumeric(info['log_offset'], param.pos), param.pos)
    return expression.BinOp(nmlop.SHIFT_LEFT, expression.ConstantNumeric(1, param.pos), param, param.pos)

def patch_variable_write(info, expr, pos):
    raise generic.ScriptError("Target parameter '%s' is not writable." % generic.reverse_lookup(patch_variables, info), pos)

def patch_variable_read(info, pos):
    expr = expression.PatchVariable(info['num'], pos)
    if info['start'] != 0:
        expr = expression.BinOp(nmlop.SHIFT_RIGHT, expr, expression.ConstantNumeric(info['start'], pos), pos)
    if info['size'] != 32:
        expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric((1 << info['size']) - 1, pos), pos)
    if 'function' in info:
        expr = info['function'](expr, info)
    return expr

def patch_variable(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(patch_variables, info), info, patch_variable_write, patch_variable_read, False, pos)

patch_variables = {
    'starting_year' : {'num': 0x0B, 'start': 0, 'size': 32, 'function': add_1920},
    'freight_trains' : {'num': 0x0E, 'start': 0, 'size': 32},
    'plane_speed' : {'num': 0x10, 'start': 0, 'size': 32},
    'base_sprite_2cc' : {'num': 0x11, 'start': 0, 'size': 32},
    'map_type' : {'num': 0x13, 'start': 24, 'size': 2},
    'map_min_edge' : {'num': 0x13, 'start': 20, 'size': 4, 'log_offset': 6, 'function': map_exponentiate},
    'map_max_edge' : {'num': 0x13, 'start': 16, 'size': 4, 'log_offset': 6, 'function': map_exponentiate},
    'map_x_edge' : {'num': 0x13, 'start': 12, 'size': 4, 'log_offset': 6, 'function': map_exponentiate},
    'map_y_edge' : {'num': 0x13, 'start': 8, 'size': 4, 'log_offset': 6, 'function': map_exponentiate},
    'map_size' : {'num': 0x13, 'start': 0, 'size': 8, 'log_offset': 12, 'function': map_exponentiate},
}

def setting_from_info(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(settings, info), info, global_param_write, global_param_read, False, pos)

cargo_numbers = {}
railtype_table = {'RAIL': 0, 'ELRL': 1, 'MONO': 1, 'MGLV': 2}
item_names = {}
settings = {}

const_list = [constant_numbers, (global_parameters, param_from_info), (misc_grf_bits, misc_grf_bit), (patch_variables, patch_variable), cargo_numbers, railtype_table, item_names, (settings, setting_from_info)]
