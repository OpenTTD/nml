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

from nml import nmlop
from nml.actions import action6, actionD, base_action, real_sprite


class ActionA(base_action.BaseAction):
    """
    Action class for Action A (sprite replacement)

    @ivar sets: List of sprite collections to be replaced.
    @type sets: C{list} of (C{int}, C{int})-tuples
    """

    def __init__(self, sets):
        self.sets = sets

    def write(self, file):
        # <Sprite-number> * <Length> 0A <num-sets> [<num-sprites> <first-sprite>]+
        size = 2 + 3 * len(self.sets)
        file.start_sprite(size)
        file.print_bytex(0x0A)
        file.print_byte(len(self.sets))
        for num, first in self.sets:
            file.print_byte(num)
            file.print_word(first)
        file.newline()
        file.end_sprite()


def parse_actionA(replaces):
    """
    Parse replace-block to ActionA.

    @param replaces: Replace-block to parse.
    @type  replaces: L{ReplaceSprite}
    """
    action_list = []
    action6.free_parameters.save()
    act6 = action6.Action6()

    real_sprite_list = real_sprite.parse_sprite_data(replaces)
    block_list = []
    total_sprites = len(real_sprite_list)
    offset = 2  # Skip 0A and <num-sets>
    sprite_offset = 0  # Number of sprites already covered by previous [<num-sprites> <first-sprite>]-pairs

    while total_sprites > 0:
        this_block = min(total_sprites, 255)  # number of sprites in this block
        total_sprites -= this_block
        offset += 1  # Skip <num-sprites>

        first_sprite = replaces.start_id  # number of first sprite
        if sprite_offset != 0:
            first_sprite = nmlop.ADD(first_sprite, sprite_offset).reduce()
        first_sprite, offset = actionD.write_action_value(first_sprite, action_list, act6, offset, 2)
        block_list.append((this_block, first_sprite.value))

        sprite_offset += this_block  # increase first-sprite for next block

    if len(act6.modifications) > 0:
        action_list.append(act6)
    action6.free_parameters.restore()

    action_list.append(ActionA(block_list))
    action_list.extend(real_sprite_list)

    return action_list
