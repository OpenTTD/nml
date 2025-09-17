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

from nml.actions import base_action, real_sprite, action2


class Action1(base_action.BaseAction):
    """
    Class representing an Action1

    @ivar feature: Feature of this action1
    @type feature: C{int}

    @ivar first_set: Number of the first sprite set in this action 1.
    @type first_set: C{int}

    @ivar num_sets: Number of (sprite) sets that follow this action 1.
    @type num_sets: C{int}

    @ivar num_ent: Number of sprites per set (e.g. (usually) 8 for vehicles)
    @type num_ent: C{int}
    """

    def __init__(self, feature, first_set, num_sets, num_ent):
        self.feature = feature
        self.first_set = first_set
        self.num_sets = num_sets
        self.num_ent = num_ent

    def write(self, file):
        if self.first_set == 0 and self.num_sets < 256:
            # <Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
            file.start_sprite(6)
            file.print_bytex(1)
            file.print_bytex(self.feature)
            file.print_byte(self.num_sets)
            file.print_varx(self.num_ent, 3)
            file.newline()
            file.end_sprite()
        else:
            # <Sprite-number> * <Length> 01 <feature> 00 <first_set> <num-sets> <num-ent>
            file.start_sprite(12)
            file.print_bytex(1)
            file.print_bytex(self.feature)
            file.print_bytex(0)
            file.print_varx(self.first_set, 3)
            file.print_varx(self.num_sets, 3)
            file.print_varx(self.num_ent, 3)
            file.newline()
            file.end_sprite()


class SpritesetCollection(base_action.BaseAction):
    """
    A collection that contains multiple spritesets. All spritesets will be
    written to the same Action1, so they need to have the same number of sprites.

    @ivar feature: The feature number the action1 will get.
    @type feature: C{int}

    @ivar first_set: Number of the first sprite set in this action 1.
    @type first_set: C{int}

    @ivar num_sprites_per_spriteset: The number of sprites in each spriteset.
    @type num_sprites_per_spriteset: C{int}

    @ivar spritesets: A mapping from spritesets to indices. This allows for
                      quick lookup of whether a spriteset is already in this
                      collection. The indices are unique integers in the
                      range 0 .. len(spritesets) - 1.
    @type spritesets: C{dict} mapping L{SpriteSet} to C{int}.
    """

    def __init__(self, feature, first_set, num_sprites_per_spriteset):
        self.feature = feature
        self.first_set = first_set
        self.num_sprites_per_spriteset = num_sprites_per_spriteset
        self.spritesets = {}
        self.max_id = 0x3FFF if feature in action2.features_sprite_layout else 0xFFFF

    def skip_action7(self):
        return False

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False

    def can_add(self, spriteset):
        """
        Test whether the given list of spritesets can be added to this collection.

        @param spriteset: The spriteset to test for addition.
        @type spriteset: L{SpriteSet}

        @return: True iff the given spriteset can be added to this collection.
        @rtype: C{bool}
        """
        assert self.first_set + 1 <= self.max_id
        if len(real_sprite.parse_sprite_data(spriteset)) != self.num_sprites_per_spriteset:
            return False
        return self.first_set + len(self.spritesets) + (1 if spriteset not in self.spritesets else 0) <= self.max_id

    def add(self, spriteset):
        """
        Add a spriteset to this collection.

        @param spriteset: The spriteset to add.
        @type spriteset: L{SpriteSet}

        @pre: can_add(spriteset).
        """
        assert self.can_add(spriteset)
        if spriteset not in self.spritesets:
            self.spritesets[spriteset] = len(self.spritesets)

    def get_index(self, spriteset):
        """
        Get the index of the given spriteset in the final action1.

        @param spriteset: The spriteset to get the index of.
        @type spriteset: L{SpriteSet}.

        @pre: The spriteset must have been previously added to this
              collection via #add.
        """
        assert spriteset in self.spritesets
        return self.first_set + self.spritesets[spriteset]

    def get_action_list(self):
        """
        Create a list of actions needed to write this collection to the output. This
        will generate a single Action1 and as many realsprites as needed.

        @return: A list of actions needed to represent this collection in a GRF.
        @rtype: C{list} of L{BaseAction}
        """
        actions = [Action1(self.feature, self.first_set, len(self.spritesets), self.num_sprites_per_spriteset)]
        for idx in range(len(self.spritesets)):
            for spriteset, spriteset_offset in self.spritesets.items():
                if idx == spriteset_offset:
                    actions.extend(real_sprite.parse_sprite_data(spriteset))
                    break
        return actions


"""
The list of collections per feature. add_to_action1 will try to reuse the
last collection as long as possible to reduce the duplication of sprites. As soon
as a spriteset with a different amount of sprites is added a new collection will
be created.
"""
spriteset_collections = {}


def add_to_action1(spritesets, feature, pos):
    """
    Add a list of spritesets to a spriteset collection. This will try to reuse
    one collection as long as possible and create a new one when needed.

    @param spritesets: List of spritesets that will be used by the next action2.
    @type spritesets: C{list} of L{SpriteSet}

    @param feature: Feature of the spritesets.
    @type feature: C{int}

    @param pos: Position reference to source.
    @type  pos: L{Position}

    @return: List of collections that needs to be added to the global action list.
    @rtype: C{list} of L{SpritesetCollection}.
    """
    if not spritesets:
        return []

    actions = []

    if feature not in spriteset_collections:
        spriteset_collections[feature] = [
            SpritesetCollection(feature, 0, len(real_sprite.parse_sprite_data(spritesets[0])))
        ]
        actions.append(spriteset_collections[feature][-1])

    current_collection = spriteset_collections[feature][-1]
    for spriteset in spritesets:
        for spriteset_collection in spriteset_collections[feature]:
            if spriteset in spriteset_collection.spritesets:
                continue
        if not current_collection.can_add(spriteset):
            spriteset_collections[feature].append(
                SpritesetCollection(
                    feature,
                    current_collection.first_set + len(current_collection.spritesets),
                    len(real_sprite.parse_sprite_data(spriteset)),
                )
            )
            current_collection = spriteset_collections[feature][-1]
            actions.append(current_collection)
        current_collection.add(spriteset)

    return actions


def get_action1_index(spriteset, feature):
    """
    Get the index of a spriteset in the action1. The given spriteset must have
    been added in the last call to #add_to_action1. Any new calls to
    #add_to_action1 may or may not allocate a new spriteset collection and as
    such make previous spritesets inaccessible.

    @param spriteset: The spriteset to get the index of.
    @type spriteset: L{SpriteSet}.

    @param feature: Feature of the spriteset.
    @type feature: C{int}

    @return: The index in the action1 of the given spriteset.
    @rtype: C{int}
    """
    assert feature in spriteset_collections
    for spriteset_collection in spriteset_collections[feature]:
        if spriteset in spriteset_collection.spritesets:
            return spriteset_collection.get_index(spriteset)
    assert False


def make_cb_failure_action1(feature):
    """
    Create an action1 that may be used for a callback failure
    If the last action1 is of the correct feature, no new action1 is needed
    Else, add a new action1 with 1 spriteset containing 0 sprites

    @param feature: Feature of the requested action 1
    @type feature: C{int}

    @return: List of actions to append (if any) and action1 index to use
    @rtype: C{tuple} of (C{list} of L{BaseAction}, C{int})
    """
    if feature in spriteset_collections:
        actions = []
    else:
        actions = [Action1(feature, 0, 1, 0)]
    return (actions, 0)  # Index is currently always 0, but will change with ext. A1
