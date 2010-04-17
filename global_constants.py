const_table = {
    #climates
    'CLIMATE_TEMPERATE'     : 0x00,
    'CLIMATE_ARCTIC'        : 0x01,
    'CLIMATE_TROPICAL'      : 0x02,
    'CLIMATE_TOYLAND'       : 0x03,
    
    'CLIMATE_BIT_NONE'      : 0x00,
    'CLIMATE_BIT_TEMPERATE' : 0x01,
    'CLIMATE_BIT_ARCTIC'    : 0x02,
    'CLIMATE_BIT_TROPICAL'  : 0x04,
    'CLIMATE_BIT_TOYLAND'   : 0x08,
    'CLIMATE_BIT_ALL'       : 0x0F,
    
    #never expire
    'VEHICLE_NEVER_EXPIRES' : 0xFF,
    
    #days up to 1920-01-01
    'DATE_1920' : 701265,
    
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
    
}
