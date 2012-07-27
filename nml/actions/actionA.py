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

from nml import expression
from nml.actions import base_action, real_sprite, actionD, action6

class ActionA(base_action.BaseAction):
    """
    Action class for Action A (sprite replacement)

    @ivar sets: List of sprite collections to be replaced.
    @type sets: C{list} of (C{int}, C{int})-tuples
    """
    def __init__(self, sets):
        self.sets = sets

    def write(self, file):
        #<Sprite-number> * <Length> 0A <num-sets> [<num-sprites> <first-sprite>]+
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
    sprite_num, offset = actionD.write_action_value(replaces.start_id, action_list, act6, 3, 2)

    if len(act6.modifications) > 0:
        action_list.append(act6)
    action6.free_parameters.restore()

    action_list.append(ActionA([(len(real_sprite_list), sprite_num.value)]))
    action_list.extend(real_sprite_list)

    return action_list

