from nml import generic, expression
from nml.actions import real_sprite
import warnings

class Action5(object):
    def __init__(self, type, num_sprites, offset):
        self.type = type
        self.num_sprites = num_sprites
        self.offset = offset

    def prepare_output(self):
        if self.offset != 0:
            self.type |= 0x80

    def write(self, file):
        #<Sprite-number> * <Length> 05 <type> <num-sprites> [<offset>]
        size = 5 if self.offset == 0 else 8
        file.start_sprite(size)
        file.print_bytex(0x05)
        file.print_bytex(self.type)
        file.print_bytex(0xFF)
        file.print_word(self.num_sprites)
        if self.offset != 0:
            file.print_bytex(0xFF)
            file.print_word(self.offset)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        #skipping with Action  should work, according to the Action7/9 specs
        #However, skipping invalid (OpenTTD-only) Action5s in TTDP can only be done using Action9, else an error occurs
        #To be on the safe side, don't allow skipping with Action7 at all
        return False

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

class Action5BlockType(object):
    FIXED  = 0, #fixed number of sprites
    ANY    = 1, #any number of sprites
    OFFSET = 2, #flexible number of sprites, offset may be set

action5_table = {
    'PRE_SIGNAL' : (0x04, 48, Action5BlockType.FIXED),
    'PRE_SIGNAL_SEMAPHORE' : (0x04, 112, Action5BlockType.FIXED),
    'PRE_SIGNAL_SEMAPHORE_PBS' : (0x04, 240, Action5BlockType.FIXED),
    'CATERNARY' : (0x05, 48, Action5BlockType.FIXED),
    'FOUNDATIONS_SLOPES' : (0x06, 74, Action5BlockType.FIXED),
    'FOUNDATIONS_SLOPES_HALFTILES' : (0x06, 90, Action5BlockType.FIXED),
    'TTDP_GUI_25' : (0x07, 73, Action5BlockType.FIXED),
    'TTDP_GUI' : (0x07, 93, Action5BlockType.FIXED),
    'CANALS' : (0x08, 65, Action5BlockType.FIXED),
    'ONE_WAY_ROAD' : (0x09, 6, Action5BlockType.FIXED),
    'COLORMAP_2CC' : (0x0A, 256, Action5BlockType.FIXED),
    'TRAMWAY' : (0x0B, 113, Action5BlockType.FIXED),
    'SNOWY_TEMPERATE_TREES' : (0x0C, 133, Action5BlockType.FIXED),
    'COAST_TILES' : (0x0D, 16, Action5BlockType.FIXED),
    'COAST_TILES_BASEGFX' : (0x0D, 10, Action5BlockType.FIXED),
    'COAST_TILES_DIAGONAL' : (0x0D, 18, Action5BlockType.FIXED),
    'NEW_SIGNALS' : (0x0E, 0, Action5BlockType.ANY),
    'SLOPED_RAILS' : (0x0F, 12, Action5BlockType.FIXED),
    'AIRPORTS' : (0x10, 15, Action5BlockType.FIXED),
    'ROAD_STOPS' : (0x11, 8, Action5BlockType.FIXED),
    'AQUEDUCTS' : (0x12, 8, Action5BlockType.FIXED),
    'AUTORAIL' : (0x13, 55, Action5BlockType.FIXED),
    'FLAGS' : (0x14, 36, Action5BlockType.OFFSET), 
    'OTTD_GUI' : (0x15, 154, Action5BlockType.OFFSET),
}

def parse_action5(replaces):
    action_list = []

    real_sprite_list = real_sprite.parse_sprite_list(replaces.sprite_list)
    num_sprites = len(real_sprite_list)

    if not isinstance(replaces.type, expression.Identifier):
        raise generic.ScriptError("replacenew parameter 'type' must be an identifier of a sprite replacement type")
    if replaces.type.value not in action5_table:
        raise generic.ScriptError(replaces.type.value + " is not a valid sprite replacement type")
    type_id, num_required, block_type = action5_table[replaces.type.value]

    try:
        offset = replaces.offset.reduce_constant().value
    except generic.ConstError:
        raise generic.ScriptError("replacenew parameter 'offset' must be a compile-time constant")
    generic.check_range(offset, 0, 0xFFFF, "replacenew parameter 'offset'")

    if block_type == Action5BlockType.FIXED:
        if num_sprites < num_required:
            raise generic.ScriptError("Invalid sprite count for sprite replacement type '%s', expcected %d, got %d" % (replaces.type, num_required, num_sprites))
        elif num_sprites > num_required:
            warnings.warn("Too many sprites specified for sprite replacement type '%s', expcected %d, got %d, extra sprites may be ignored" % (replaces.type, num_required, num_sprites))
        if offset != 0:
            raise generic.ScriptError("replacenew parameter 'offset' must be zero for sprite replacement type '%s'" % replaces.type)
    elif block_type == Action5BlockType.ANY:
        if offset != 0:
            raise generic.ScriptError("replacenew parameter 'offset' must be zero for sprite replacement type '%s'" % replaces.type)
    elif block_type == Action5BlockType.OFFSET:
        if num_sprites + offset > num_required:
            warnings.warn("Exceeding the limit of %d spriets for sprite replacement type '%s', extra sprites may be ignored" % (num_required, replaces.type))
    else:
        assert 0

    action_list.append(Action5(type_id, num_sprites, offset))

    last_sprite = real_sprite_list[-1][0]
    for sprite, id_dict in real_sprite_list:
        action_list.append(real_sprite.parse_real_sprite(sprite, replaces.pcx, sprite == last_sprite, id_dict))

    return action_list
