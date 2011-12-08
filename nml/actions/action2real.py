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
from nml.actions import action2, action1
from nml.ast import general

class Action2Real(action2.Action2):
    def __init__(self, feature, name, loaded_list, loading_list):
        action2.Action2.__init__(self, feature, name)
        self.loaded_list = loaded_list
        self.loading_list = loading_list

    def write(self, file):
        size = 2 + 2 * len(self.loaded_list) + 2 * len(self.loading_list)
        action2.Action2.write_sprite_start(self, file, size)
        file.print_byte(len(self.loaded_list))
        file.print_byte(len(self.loading_list))
        file.newline()
        for i in self.loaded_list:
            file.print_word(i)
        file.newline()
        for i in self.loading_list:
            file.print_word(i)
        file.newline()
        file.end_sprite()

def get_real_action2s(spritegroup, feature):
    loaded_list = []
    loading_list = []
    actions = []

    if feature not in action2.features_sprite_group:
        raise generic.ScriptError("Sprite groups that combine sprite sets are not supported for feature '%s'." % general.feature_name(feature), spritegroup.pos)

    # First make sure that all referenced real sprites are put in a single action1
    spriteset_list = []
    for view in spritegroup.spriteview_list:
        spriteset_list.extend([action2.resolve_spritegroup(sg_ref.name) for sg_ref in view.spriteset_list])
    actions.extend(action1.add_to_action1(spriteset_list, feature, spritegroup.pos))

    view_names = sorted([view.name.value for view in spritegroup.spriteview_list])
    if feature in (0x00, 0x01, 0x02, 0x03):
        if view_names != sorted(['loading', 'loaded']):
            raise generic.ScriptError("Expected a 'loading' and a 'loaded' (list of) sprite set(s).", spritegroup.pos)
    elif feature in (0x05, 0x0B, 0x0D, 0x10):
        generic.print_warning("Sprite groups for feature %02X will not be supported in the future, as they are no longer needed. Directly refer to sprite sets instead." % feature, spritegroup.pos)
        if view_names != ['default']:
            raise generic.ScriptError("Expected only a 'default' (list of) sprite set(s).", spritegroup.pos)

    for view in spritegroup.spriteview_list:
        if len(view.spriteset_list) == 0:
            raise generic.ScriptError("Expected at least one sprite set, encountered 0.", view.pos)
        for set_ref in view.spriteset_list:
            spriteset = action2.resolve_spritegroup(set_ref.name)
            action1_index = action1.get_action1_index(spriteset)
            if view.name.value == 'loading': loading_list.append(action1_index)
            else: loaded_list.append(action1_index)

    actions.append(Action2Real(feature, spritegroup.name.value + (" - feature %02X" % feature), loaded_list, loading_list))
    spritegroup.set_action2(actions[-1], feature)
    return actions

def create_spriteset_actions(spritegroup):
    """
    Create action2s for directly-referenced sprite sets

    @param spritegroup: Spritegroup to create the sprite sets for
    @type spritegroup: L{ASTSpriteGroup}

    @return: Resulting list of actions
    @rtype: C{list} of L{BaseAction}
    """
    action_list = []
    # Iterate over features first for more efficient action1s
    for feature in spritegroup.feature_set:
        if len(spritegroup.used_sprite_sets) != 0 and feature not in action2.features_sprite_group:
            raise generic.ScriptError("Directly referring to sprite sets is not possible for feature %02X" % feature, spritegroup.pos)
        for spriteset in spritegroup.used_sprite_sets:
            if spriteset.has_action2(feature): continue
            action_list.extend(action1.add_to_action1([spriteset], feature, spritegroup.pos))
            action1_index = action1.get_action1_index(spriteset)
            real_action2 = Action2Real(feature, spriteset.name.value + (" - feature %02X" % feature), [action1_index], [action1_index] if feature <= 0x03 else [])
            action_list.append(real_action2)
            spriteset.set_action2(real_action2, feature)
    return action_list
