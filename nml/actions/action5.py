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

from nml import generic
from nml.actions import base_action, real_sprite

class Action5(base_action.BaseAction):
    def __init__(self, type, num_sprites, offset):
        self.type = type
        self.num_sprites = num_sprites
        self.offset = offset

    def prepare_output(self):
        if self.offset is not None:
            self.type |= 0x80

    def write(self, file):
        #<Sprite-number> * <Length> 05 <type> <num-sprites> [<offset>]
        size = 5 if self.offset is None else 8
        file.start_sprite(size)
        file.print_bytex(0x05)
        file.print_bytex(self.type)
        file.print_bytex(0xFF)
        file.print_word(self.num_sprites)
        if self.offset is not None:
            file.print_bytex(0xFF)
            file.print_word(self.offset)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        #skipping with Action7 should work, according to the Action7/9 specs
        #However, skipping invalid (OpenTTD-only) Action5s in TTDP can only be done using Action9, else an error occurs
        #To be on the safe side, don't allow skipping with Action7 at all
        return False

class Action5BlockType(object):
    FIXED  = 0, #fixed number of sprites
    ANY    = 1, #any number of sprites
    OFFSET = 2, #flexible number of sprites, offset may be set

action5_table = {
    'PRE_SIGNAL' : (0x04, 48, Action5BlockType.FIXED),
    'PRE_SIGNAL_SEMAPHORE' : (0x04, 112, Action5BlockType.FIXED),
    'PRE_SIGNAL_SEMAPHORE_PBS' : (0x04, 240, Action5BlockType.OFFSET),
    'CATENARY' : (0x05, 48, Action5BlockType.OFFSET),
    'FOUNDATIONS_SLOPES' : (0x06, 74, Action5BlockType.FIXED),
    'FOUNDATIONS_SLOPES_HALFTILES' : (0x06, 90, Action5BlockType.OFFSET),
    'TTDP_GUI_25' : (0x07, 73, Action5BlockType.FIXED),
    'TTDP_GUI' : (0x07, 93, Action5BlockType.FIXED),
    'CANALS' : (0x08, 65, Action5BlockType.OFFSET),
    'ONE_WAY_ROAD' : (0x09, 6, Action5BlockType.OFFSET),
    'COLOURMAP_2CC' : (0x0A, 256, Action5BlockType.OFFSET),
    'TRAMWAY' : (0x0B, 113, Action5BlockType.OFFSET),
    'SNOWY_TEMPERATE_TREES' : (0x0C, 133, Action5BlockType.FIXED),
    'COAST_TILES' : (0x0D, 16, Action5BlockType.FIXED),
    'COAST_TILES_BASEGFX' : (0x0D, 10, Action5BlockType.FIXED),
    'COAST_TILES_DIAGONAL' : (0x0D, 18, Action5BlockType.FIXED),
    'NEW_SIGNALS' : (0x0E, 0, Action5BlockType.ANY),
    'SLOPED_RAILS' : (0x0F, 12, Action5BlockType.OFFSET),
    'AIRPORTS' : (0x10, 15, Action5BlockType.OFFSET),
    'ROAD_STOPS' : (0x11, 8, Action5BlockType.OFFSET),
    'AQUEDUCTS' : (0x12, 8, Action5BlockType.OFFSET),
    'AUTORAIL' : (0x13, 55, Action5BlockType.OFFSET),
    'FLAGS' : (0x14, 36, Action5BlockType.OFFSET),
    'OTTD_GUI' : (0x15, 162, Action5BlockType.OFFSET),
    'AIRPORT_PREVIEW' : (0x16, 9, Action5BlockType.OFFSET),
}

def parse_action5(replaces):
    real_sprite_list = real_sprite.parse_sprite_list(replaces.sprite_list, replaces.pcx, block_name = replaces.name)
    num_sprites = len(real_sprite_list)

    if replaces.type.value not in action5_table:
        raise generic.ScriptError(replaces.type.value + " is not a valid sprite replacement type", replaces.type.pos)
    type_id, num_required, block_type = action5_table[replaces.type.value]
    offset = None

    if block_type == Action5BlockType.FIXED:
        if num_sprites < num_required:
            raise generic.ScriptError("Invalid sprite count for sprite replacement type '%s', expcected %d, got %d" % (replaces.type, num_required, num_sprites), replaces.pos)
        elif num_sprites > num_required:
            generic.print_warning("Too many sprites specified for sprite replacement type '%s', expcected %d, got %d, extra sprites may be ignored" % (replaces.type, num_required, num_sprites), replaces.pos)
        if replaces.offset != 0:
            raise generic.ScriptError("replacenew parameter 'offset' must be zero for sprite replacement type '%s'" % replaces.type, replaces.pos)
    elif block_type == Action5BlockType.ANY:
        if replaces.offset != 0:
            raise generic.ScriptError("replacenew parameter 'offset' must be zero for sprite replacement type '%s'" % replaces.type, replaces.pos)
    elif block_type == Action5BlockType.OFFSET:
        if num_sprites + replaces.offset > num_required:
            generic.print_warning("Exceeding the limit of %d spriets for sprite replacement type '%s', extra sprites may be ignored" % (num_required, replaces.type), replaces.pos)
        if replaces.offset != 0 or num_sprites != num_required:
            offset = replaces.offset
    else:
        assert 0

    return [Action5(type_id, num_sprites, offset)] + real_sprite_list
