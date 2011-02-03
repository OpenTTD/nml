from nml import expression, generic, nmlop

constant_numbers = {
    #climates
    'CLIMATE_TEMPERATE'     : 0,
    'CLIMATE_ARCTIC'        : 1,
    'CLIMATE_TROPIC'        : 2,
    'CLIMATE_TROPICAL'      : 2,
    'CLIMATE_TOYLAND'       : 3,
    'ABOVE_SNOWLINE'        : 11, # Only for house property available_mask

    'NO_CLIMATE'            : 0x00,
    'ALL_CLIMATES'          : 0x0F,

    #never expire
    'VEHICLE_NEVER_EXPIRES' : 0xFF,

    #cargo classes
    'CC_PASSENGERS'   : 0,
    'CC_MAIL'         : 1,
    'CC_EXPRESS'      : 2,
    'CC_ARMOURED'     : 3,
    'CC_BULK'         : 4,
    'CC_PIECE_GOODS'  : 5,
    'CC_LIQUID'       : 6,
    'CC_REFRIGERATED' : 7,
    'CC_HAZARDOUS'    : 8,
    'CC_COVERED'      : 9,
    'CC_OVERSIZED'    : 10,
    'CC_SPECIAL'      : 15,
    'NO_CARGO_CLASS'           : 0,
    'ALL_NORMAL_CARGO_CLASSES' : 0x07FF,
    'ALL_CARGO_CLASSES'        : 0x87FF,

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
    'VEH_CBF_VISUAL_EFFECT_AND_POWERED' : 0,
    'VEH_CBF_WAGON_LENGTH'              : 1,
    'VEH_CBF_LOAD_AMOUNT'               : 2,
    'VEH_CBF_REFITTED_CAPACITY'         : 3,
    'VEH_CBF_ARTICULATED_PARTS'         : 4,
    'VEH_CBF_CARGO_SUFFIX'              : 5,
    'VEH_CBF_COLOUR_MAPPING'            : 6,
    'VEH_CBF_SOUND_EFFECT'              : 7,

    #corresponding callbacks
    'VEH_CB_VISUAL_EFFECT_AND_POWERED'  : 0x10,
    'VEH_CB_WAGON_LENGTH'               : 0x11,
    'VEH_CB_LOAD_AMOUNT'                : 0x12,
    'VEH_CB_REFITTED_CAPACITY'          : 0x15,
    'VEH_CB_ARTICULATED_PARTS'          : 0x16,
    'VEH_CB_CARGO_SUFFIX'               : 0x19,
    'VEH_CB_CAN_ATTACH_WAGON'           : 0x1D,
    'VEH_CB_TEXT_PURCHASE_SCREEN'       : 0x23,
    'VEH_CB_COLOUR_MAPPING'             : 0x2D,
    'VEH_CB_START_STOP_CHECK'           : 0x31,
    'VEH_CB_32DAY'                      : 0x32,
    'VEH_CB_SOUND_EFFECT'               : 0x33,
    'VEH_CB_AUTOREPLACE_SELECT'         : 0x34,
    'VEH_CB_VEHICLE_PROPERTIES'         : 0x36,

    #properties for callback 0x36
    'PROP_TRAINS_SPEED'                         : 0x09,
    'PROP_TRAINS_POWER'                         : 0x0B,
    'PROP_TRAINS_RUNNING_COST_FACTOR'           : 0x0D,
    'PROP_TRAINS_CARGO_CAPACITY'                : 0x14,
    'PROP_TRAINS_WEIGHT'                        : 0x16,
    'PROP_TRAINS_COST_FACTOR'                   : 0x17,
    'PROP_TRAINS_TRACTIVE_EFFORT_COEFFICIENT'   : 0x1F,
    'PROP_TRAINS_BITMASK_VEHICLE_INFO'          : 0x25,

    'PROP_ROADVEHS_RUNNING_COST_FACTOR'         : 0x09,
    'PROP_ROADVEHS_CARGO_CAPACITY'              : 0x0F,
    'PROP_ROADVEHS_COST_FACTOR'                 : 0x11,
    'PROP_ROADVEHS_POWER'                       : 0x13,
    'PROP_ROADVEHS_WEIGHT'                      : 0x14,
    'PROP_ROADVEHS_SPEED'                       : 0x15,
    'PROP_ROADVEHS_TRACTIVE_EFFORT_COEFFICIENT' : 0x18,

    'PROP_SHIPS_COST_FACTOR'                    : 0x0A,
    'PROP_SHIPS_SPEED'                          : 0x0B,
    'PROP_SHIPS_CARGO_CAPACITY'                 : 0x0D,
    'PROP_SHIPS_RUNNING_COST_FACTOR'            : 0x0F,

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
    'ENABLE_WAGON_POWER'     : 0x00,
    'DISABLE_WAGON_POWER'    : 0x80,

    #train misc flags
    'TRAIN_FLAG_TILT' : 0,
    'TRAIN_FLAG_2CC'  : 1,
    'TRAIN_FLAG_MU'   : 2,

    #roadveh misc flags
    'ROADVEH_FLAG_TRAM' : 0,
    'ROADVEH_FLAG_2CC'  : 1,

    #ship misc flags
    'SHIP_FLAG_2CC'  : 1,

    #aircrafts misc flags
    'AIRCRAFT_FLAG_2CC'  : 1,

    #for those, who can't tell the difference between a train and an aircraft:
    'VEHICLE_FLAG_2CC' : 1,

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
    'HOUSE_CBF_BUILD'               : 0,
    'HOUSE_CBF_ANIM_NEXT_FRAME'     : 1,
    'HOUSE_CBF_ANIM_STARTSTOP'      : 2,
    'HOUSE_CBF_CONSTRUCTION_ANIM'   : 3,
    'HOUSE_CBF_COLOUR'              : 4,
    'HOUSE_CBF_CARGO_AMOUNT_ACCEPT' : 5,
    'HOUSE_CBF_ANIM_FRAME_LENGTH'   : 6,
    'HOUSE_CBF_DESTRUCTION'         : 7,
    'HOUSE_CBF_CARGO_TYPE_ACCEPT'   : 8,
    'HOUSE_CBF_CARGO_PRODUCTION'    : 9,
    'HOUSE_CBF_PROTECTION'          : 10,
    'HOUSE_CBF_FOUNDATIONS'         : 11,
    'HOUSE_CBF_AUTOSLOPE'           : 12,

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
    'HOUSE_FLAG_SIZE_1x1'           : 0,
    'HOUSE_FLAG_NOT_SLOPED'         : 1,
    'HOUSE_FLAG_SIZE_2x1'           : 2,
    'HOUSE_FLAG_SIZE_1x2'           : 3,
    'HOUSE_FLAG_SIZE_2x2'           : 4,
    'HOUSE_FLAG_ANIMATE'            : 5,
    'HOUSE_FLAG_CHURCH'             : 6,
    'HOUSE_FLAG_STADIUM'            : 7,
    'HOUSE_FLAG_ONLY_SE'            : 8,
    'HOUSE_FLAG_PROTECTED'          : 9,
    'HOUSE_FLAG_SYNC_CALLBACK'      : 10,
    'HOUSE_FLAG_RANDOM_ANIMATION'   : 11,

    #cargo acceptance
    'HOUSE_ACCEPT_GOODS'            : 0x00,
    'HOUSE_ACCEPT_FOOD'             : 0x10, # 0x80 / 8
    'HOUSE_ACCEPT_FIZZY_DRINKS'     : 0x10, # 0x80 / 8

    #town zones
    'TOWNZONE_EDGE'                 : 0,
    'TOWNZONE_OUTSKIRT'             : 1,
    'TOWNZONE_OUTER_SUBURB'         : 2,
    'TOWNZONE_INNER_SUBURB'         : 3,
    'TOWNZONE_CENTRE'               : 4,
    'ALL_TOWNZONES'                 : 0x1F,

    #industry tile callback flags
    'INDTILE_CBF_ANIM_NEXT_FRAME'     : 0,
    'INDTILE_CBF_ANIM_SPEED'          : 1,
    'INDTILE_CBF_CARGO_AMOUNT_ACCEPT' : 2,
    'INDTILE_CBF_CARGO_TYPE_ACCEPT'   : 3,
    'INDTILE_CBF_SLOPE_IS_SUITABLE'   : 4,
    'INDTILE_CBF_FOUNDATIONS'         : 5,
    'INDTILE_CBF_AUTOSLOPE'           : 6,

    #corresponding callbacks
    'INDTILE_CB_ANIM_STARTSTOP'       : 0x25,
    'INDTILE_CB_ANIM_NEXT_FRAME'      : 0x26,
    'INDTILE_CB_ANIM_SPEED'           : 0x27,
    'INDTILE_CB_CARGO_AMOUNT_ACCEPT'  : 0x2B,
    'INDTILE_CB_CARGO_TYPE_ACCEPT'    : 0x2C,
    'INDTILE_CB_SLOPE_IS_SUITABLE'    : 0x2F,
    'INDTILE_CB_FOUNDATIONS'          : 0x30,
    'INDTILE_CB_AUTOSLOPE'            : 0x3F,

    #Triggers for the animation start/stop callback
    'INDTILE_TRIGGER_CONSTRUCTION_STATE'         : 0,
    'INDTILE_TRIGGER_TILE_LOOP'                  : 1,
    'INDTILE_TRIGGER_INDUSTRY_LOOP'              : 2,
    'INDTILE_TRIGGER_INDUSTRY_RECEIVED_CARGO'    : 3,
    'INDTILE_TRIGGER_INDUSTRY_DISTRIBUTES_CARGO' : 4,

    #industry callback flags
    'IND_CBF_AVAILABILITY'          : 0,
    'IND_CBF_PROD_CB_CARGO_ARRIVE'  : 1,
    'IND_CBF_PROD_CB_256_TICKS'     : 2,
    'IND_CBF_LOCATION_CHECK'        : 3,
    'IND_CBF_RANDOM_PROD_CHANGE'    : 4,
    'IND_CBF_MONTLY_PROD_CHANGE'    : 5,
    'IND_CBF_CARGO_SUBTYPE_DISPLAY' : 6,
    'IND_CBF_EXTRA_TEXT_FUND'       : 7,
    'IND_CBF_EXTRA_TEXT_INDUSTRY'   : 8,
    'IND_CBF_CONTROL_SPECIAL'       : 9,
    'IND_CBF_STOP_ACCEPT_CARGO'     : 10,
    'IND_CBF_COLOUR'                 : 11,
    'IND_CBF_CARGO_INPUT'           : 12,
    'IND_CBF_CARGO_OUTPUT'          : 13,

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
    'IND_CB_COLOUR'                  : 0x14A,
    'IND_CB_CARGO_INPUT'            : 0x14B,
    'IND_CB_CARGO_OUTPUT'           : 0x14C,

    #industry special flags
    'IND_FLAG_PLANT_FIELDS_PERIODICALLY'               : 0,
    'IND_FLAG_CUT_TREES'                               : 1,
    'IND_FLAG_BUILT_ON_WATER'                          : 2,
    'IND_FLAG_ONLY_IN_LARGE_TOWNS'                     : 3,
    'IND_FLAG_ONLY_IN_TOWNS'                           : 4,
    'IND_FLAG_BUILT_NEAR_TOWN'                         : 5,
    'IND_FLAG_PLANT_FIELDS_WHEN_BUILT'                 : 6,
    'IND_FLAG_NO_PRODUCTION_INCREASE'                  : 7,
    'IND_FLAG_BUILT_ONLY_BEFORE_1950'                  : 8,
    'IND_FLAG_BUILT_ONLY_AFTER_1960'                   : 9,
    'IND_FLAG_AI_CREATES_AIR_AND_SHIP_ROUTES'          : 10,
    'IND_FLAG_MILITARY_AIRPLANE_CAN_EXPLODE'           : 11,
    'IND_FLAG_MILITARY_HELICOPTER_CAN_EXPLODE'         : 12,
    'IND_FLAG_CAN_CAUSE_SUBSIDENCE'                    : 13,
    'IND_FLAG_AUTOMATIC_PRODUCTION_MULTIPLIER'         : 14,
    'IND_FLAG_RANDOM_BITS_IN_PRODUCTION_CALLBACK'      : 15,
    'IND_FLAG_DO_NOT_FORCE_INSTANCE_AT_MAP_GENERATION' : 16,
    'IND_FLAG_ALLOW_CLOSING_LAST_INSTANCE'             : 17,

    #object flags
    'OBJ_FLAG_ONLY_SE'         : 0,
    'OBJ_FLAG_IRREMOVABLE'     : 1,
    'OBJ_FLAG_ANYTHING_REMOVE' : 2,
    'OBJ_FLAG_ON_WATER'        : 3,
    'OBJ_FLAG_REMOVE_IS_INCOME': 4,
    'OBJ_FLAG_NO_FOUNDATIONS'  : 5,
    'OBJ_FLAG_ANIMATED'        : 6,
    'OBJ_FLAG_ONLY_INGAME'     : 7,
    'OBJ_FLAG_2CC'             : 8,
    'OBJ_FLAG_NOT_ON_LAND'     : 9,
    'OBJ_FLAG_DRAW_WATER'      : 10,
    'OBJ_FLAG_ALLOW_BRIDGE'    : 11,
    'OBJ_FLAG_RANDOM_ANIMATION': 12,

    #object animation triggers
    'OBJ_ANIM_IS_BUILT'        : 0,
    'OBJ_ANIM_PERIODIC'        : 1,
    'OBJ_ANIM_SYNC'            : 2,

    #object callback flags
    'OBJ_CBF_SLOPE_CHECK'      : 0,
    'OBJ_CBF_DECIDE_ANIM'      : 1,
    'OBJ_CBF_DECIDE_ANIM_SPEED': 2,
    'OBJ_CBF_DECIDE_COLOUR'    : 3,
    'OBJ_CBF_ADDITIONAL_TEXT'  : 4,
    'OBJ_CBF_AUTOSLOPE'        : 5,

    #corresponding callbacks
    'OBJ_CB_SLOPE_CHECK'            : 0x157,
    'OBJ_CB_DECIDE_ANIM'            : 0x158,
    'OBJ_CB_DECIDE_ANIM_SPEED'      : 0x159,
    'OBJ_CB_DECIDE_ANIM_LENGTH'     : 0x15A,
    'OBJ_CB_DECIDE_COLOUR'          : 0x15B,
    'OBJ_CB_ADDITIONAL_TEXT'        : 0x15C,
    'OBJ_CB_AUTOSLOPE'              : 0x15D,

    #airport tile callback flags
    'APT_CBF_DECIDE_ANIM'       : 0,
    'APT_CBF_DECIDE_ANIM_SPEED' : 1,
    'APT_CBF_SLOPE_CHECK'       : 4,
    'APT_CBF_FOUNDATIONS'       : 5,
    'APT_CBF_AUTOSLOPE'         : 6,

    #corresponding callbacks
    'APT_CB_DECIDE_ANIM'        : 0x153,
    'APT_CB_DECIDE_ANIM_SPEED'  : 0x154,
    'APT_CB_FOUNDATIONS'        : 0x150,

    #railtype flags
    'RAILTYPE_FLAG_CATENARY'          : 0,
    'RAILTYPE_FLAG_NO_LEVEL_CROSSING' : 1, # for OpenTTD > r20049

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
    'INDUSTRYTYPE_TROPICAL_ARCTIC_BANK'  : 0x10,
    'INDUSTRYTYPE_DIAMOND_MINE'          : 0x11,
    'INDUSTRYTYPE_IRON_ORE_MINE'         : 0x12,
    'INDUSTRYTYPE_FRUIT_PLANTATION'      : 0x13,
    'INDUSTRYTYPE_RUBBER_PLANTATION'     : 0x14,
    'INDUSTRYTYPE_WATER_WELL'            : 0x15,
    'INDUSTRYTYPE_WATER_TOWER'           : 0x16,
    'INDUSTRYTYPE_TROPICAL_FACTORY'      : 0x17,
    'INDUSTRYTYPE_TROPICAL_FARM'         : 0x18,
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
    'TRIGGER_ALL_NEEDED'                    : 7,

    'TRIGGER_VEHICLE_NEW_LOAD'              : 0,
    'TRIGGER_VEHICLE_SERVICE'               : 1,
    'TRIGGER_VEHICLE_UNLOAD_ALL'            : 2,
    'TRIGGER_VEHICLE_ANY_LOAD'              : 3,
    'TRIGGER_VEHICLE_32_CALLBACK'           : 4,

    'TRIGGER_STATION_NEW_CARGO'             : 0,
    'TRIGGER_STATION_NO_MORE_CARGO'         : 1,
    'TRIGGER_STATION_TRAIN_ARRIVES'         : 2,
    'TRIGGER_STATION_TRAIN_LEAVES'          : 3,
    'TRIGGER_STATION_TRAIN_LOADS_UNLOADS'   : 4,
    'TRIGGER_STATION_TRAIN_RESERVES'        : 5,

    'TRIGGER_HOUSE_TILELOOP'                : 0,
    'TRIGGER_HOUSE_TOP_TILELOOP'            : 1,

    'TRIGGER_INDUSTRYTILE_TILELOOP'         : 0,
    'TRIGGER_INDUSTRYTILE_256_TICKS'        : 1,
    'TRIGGER_INDUSTRYTILE_CARGO_DELIVERY'   : 2,

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

    #Land shape flags for industry tiles
    'LSF_CANNOT_LOWER_NW_EDGE'              : 0,
    'LSF_CANNOT_LOWER_NE_EDGE'              : 1,
    'LSF_CANNOT_LOWER_SW_EDGE'              : 2,
    'LSF_CANNOT_LOWER_SE_EDGE'              : 3,
    'LSF_ONLY_ON_FLAT_LAND'                 : 4,
    'LSF_ALLOW_ON_WATER'                    : 5,

    # Animation looping
    'ANIMATION_NON_LOOPING'                 : 0,
    'ANIMATION_LOOPING'                     : 1,

    #Zoom levels
    'ZOOM_LEVEL_NORMAL'                     : 2,
    'ZOOM_LEVEL_Z0'                         : 0,
    'ZOOM_LEVEL_Z1'                         : 1,
    'ZOOM_LEVEL_Z2'                         : 2,

    #Transparant recolouring
    'TRANSPARANT'                           : -1,

    # Town growth effect of cargo
    'TOWNGROWTH_PASSENGERS'                 : 0x00,
    'TOWNGROWTH_MAIL'                       : 0x02,
    'TOWNGROWTH_GOODS'                      : 0x05,
    'TOWNGROWTH_WATER'                      : 0x09,
    'TOWNGROWTH_FOOD'                       : 0x0B,
    'TOWNGROWTH_NONE'                       : 0xFF,

    # Cargo callbacks
    'CARGO_CB_PROFIT'                       : 0x01,
    'CARGO_CB_STATION_RATING'               : 0x02,
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

def add_1920(expr, info):
    """
    Create a new expression that adds 1920 to a given expression.

    @param expr: The expression to add 1920 to.
    @type expr: L{Expression}

    @param info: Ignored.

    @return: A new expression that adds 1920 to the given expression.
    @rtype: L{Expression}
    """
    return expression.BinOp(nmlop.ADD, expr, expression.ConstantNumeric(1920, expr.pos), expr.pos)

def map_exponentiate(expr, info):
    """
    Given a exponent, add an offset ot it and compute the exponentiation with base 2.

    @param expr: The exponent.
    @type expr: L{Expression}

    @param info: Table with extra information, most notable 'log_offset', the value we need to
                 add to the given expression before computing the exponentiation.
    @type info: C{dict}

    @return: An expression computing 2**(expr + info['log_offset']).
    @rtype: L{Expression}
    """
    #map (log2(x) - a) to x, i.e. do 1 << (x + a)
    expr = expression.BinOp(nmlop.ADD, expr, expression.ConstantNumeric(info['log_offset'], expr.pos), expr.pos)
    return expression.BinOp(nmlop.SHIFT_LEFT, expression.ConstantNumeric(1, expr.pos), expr, expr.pos)

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
    expr = expression.PatchVariable(info['num'], pos)
    if info['start'] != 0:
        expr = expression.BinOp(nmlop.SHIFT_RIGHT, expr, expression.ConstantNumeric(info['start'], pos), pos)
    if info['size'] != 32:
        expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric((1 << info['size']) - 1, pos), pos)
    if 'function' in info:
        expr = info['function'](expr, info)
    return expr

def patch_variable(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(patch_variables, info), info, None, patch_variable_read, False, pos)

patch_variables = {
    'starting_year'   : {'num': 0x0B, 'start':  0, 'size': 32, 'function': add_1920},
    'freight_trains'  : {'num': 0x0E, 'start':  0, 'size': 32},
    'plane_speed'     : {'num': 0x10, 'start':  0, 'size': 32},
    'base_sprite_2cc' : {'num': 0x11, 'start':  0, 'size': 32},
    'map_type'        : {'num': 0x13, 'start': 24, 'size':  2},
    'map_min_edge'    : {'num': 0x13, 'start': 20, 'size':  4, 'log_offset':  6, 'function': map_exponentiate},
    'map_max_edge'    : {'num': 0x13, 'start': 16, 'size':  4, 'log_offset':  6, 'function': map_exponentiate},
    'map_x_edge'      : {'num': 0x13, 'start': 12, 'size':  4, 'log_offset':  6, 'function': map_exponentiate},
    'map_y_edge'      : {'num': 0x13, 'start':  8, 'size':  4, 'log_offset':  6, 'function': map_exponentiate},
    'map_size'        : {'num': 0x13, 'start':  0, 'size':  8, 'log_offset': 12, 'function': map_exponentiate},
}

def config_flag_read(bit, pos):
    return expression.BinOp(nmlop.HASBIT, expression.Parameter(expression.ConstantNumeric(0x85), pos), expression.ConstantNumeric(bit), pos)

def config_flag(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(config_flags, info), info, None, config_flag_read, True, pos)

config_flags = {
    'long_bridges'            : 0x0F,
    'gradual_loading'         : 0x2C,
    'bridge_speed_limits'     : 0x34,
    'newtrains'               : 0x37,
    'newrvs'                  : 0x38,
    'newships'                : 0x39,
    'newplanes'               : 0x3A,
    'signals_on_traffic_side' : 0x3B,
    'electrified_railways'    : 0x3C,
    'newhouses'               : 0x59,
    'newindustries'           : 0x67,
    'temperate_snowline'      : 0x6A,
    'newcargos'               : 0x6B,
    'dynamic_engines'         : 0x78,
    'variable_runningcosts'   : 0x7E,
}

def unified_maglev_read(info, pos):
    bit0 = expression.BinOp(nmlop.HASBIT, expression.Parameter(expression.ConstantNumeric(0x85), pos), expression.ConstantNumeric(0x32), pos)
    bit1 = expression.BinOp(nmlop.HASBIT, expression.Parameter(expression.ConstantNumeric(0x85), pos), expression.ConstantNumeric(0x33), pos)
    shifted_bit1 = expression.BinOp(nmlop.SHIFT_LEFT, bit1, expression.ConstantNumeric(1))
    return expression.BinOp(nmlop.OR, shifted_bit1, bit0)

def unified_maglev(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(unified_maglev_var, info), info, None, unified_maglev_read, False, pos)

unified_maglev_var = {
    'unified_maglev' : 0,
}

def setting_from_info(info, pos):
    return expression.SpecialParameter(generic.reverse_lookup(settings, info), info, global_param_write, global_param_read, False, pos)

cargo_numbers = {}
railtype_table = {'RAIL': 0, 'ELRL': 1, 'MONO': 1, 'MGLV': 2}
item_names = {}
settings = {}

const_list = [constant_numbers, (global_parameters, param_from_info), (misc_grf_bits, misc_grf_bit), (patch_variables, patch_variable), cargo_numbers, railtype_table, item_names, (settings, setting_from_info), (config_flags, config_flag), (unified_maglev_var, unified_maglev)]
