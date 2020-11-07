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

"""
Maximum number of sprites per block.
This can be increased by switching to extended Action1.
"""
max_sprite_block_size = 0xFF


class Action1(base_action.BaseAction):
    """
    Class representing an Action1

    @ivar feature: Feature of this action1
    @type feature: C{int}

    @ivar num_sets: Number of (sprite) sets that follow this action 1.
    @type num_sets: C{int}

    @ivar num_ent: Number of sprites per set (e.g. (usually) 8 for vehicles)
    @type num_ent: C{int}
    """

    def __init__(self, feature, num_sets, num_ent):
        self.feature = feature
        self.num_sets = num_sets
        self.num_ent = num_ent

    def write(self, file):
        # <Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
        file.start_sprite(6)
        file.print_bytex(1)
        file.print_bytex(self.feature)
        file.print_byte(self.num_sets)
        file.print_varx(self.num_ent, 3)
        file.newline()
        file.end_sprite()


class SpritesetCollection(base_action.BaseAction):
    """
    A collection that contains multiple spritesets. All spritesets will be
    written to the same Action1, so they need to have the same number of sprites.

    @ivar feature: The feature number the action1 will get.
    @type feature: C{int}

    @ivar num_sprites_per_spriteset: The number of sprites in each spriteset.
    @type num_sprites_per_spriteset: C{int}

    @ivar spritesets: A mapping from spritesets to indices. This allows for
                      quick lookup of whether a spriteset is already in this
                      collection. The indices are unique integers in the
                      range 0 .. len(spritesets) - 1.
    @type spritesets: C{dict} mapping L{SpriteSet} to C{int}.
    """

    def __init__(self, feature, num_sprites_per_spriteset):
        self.feature = feature
        self.num_sprites_per_spriteset = num_sprites_per_spriteset
        self.spritesets = {}

    def skip_action7(self):
        return False

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False

    def can_add(self, spritesets, feature):
        """
        Test whether the given list of spritesets can be added to this collection.

        @param spritesets: The list of spritesets to test for addition.
        @type spritesets: C{list} of L{SpriteSet}

        @param feature: The feature of the given spritesets.
        @type feature: C{int}

        @return: True iff the given spritesets can be added to this collection.
        @rtype: C{bool}
        """
        assert len(spritesets) <= max_sprite_block_size
        if feature != self.feature:
            return False
        for spriteset in spritesets:
            if len(real_sprite.parse_sprite_data(spriteset)) != self.num_sprites_per_spriteset:
                return False
        num_new_sets = sum(1 for x in spritesets if x not in self.spritesets)
        return len(self.spritesets) + num_new_sets <= max_sprite_block_size

    def add(self, spritesets):
        """
        Add a list of spritesets to this collection.

        @param spritesets: The list of spritesets to add.
        @type spritesets: C{list} of L{SpriteSet}

        @pre: can_add(spritesets, self.feature).
        """
        assert self.can_add(spritesets, self.feature)
        for spriteset in spritesets:
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
        return self.spritesets[spriteset]

    def get_action_list(self):
        """
        Create a list of actions needed to write this collection to the output. This
        will generate a single Action1 and as many realsprites as needed.

        @return: A list of actions needed to represet this collection in a GRF.
        @rtype: C{list} of L{BaseAction}
        """
        actions = [Action1(self.feature, len(self.spritesets), self.num_sprites_per_spriteset)]
        for idx in range(len(self.spritesets)):
            for spriteset, spriteset_offset in self.spritesets.items():
                if idx == spriteset_offset:
                    actions.extend(real_sprite.parse_sprite_data(spriteset))
                    break
        return actions


"""
Statistics about spritesets.
The 1st field of type C{int} contains the largest block of consecutive spritesets.
The 2nd field of type L{Position} contains a positional reference to the largest block of consecutive spritesets.
"""
spriteset_stats = (0, None)


def print_stats():
    """
    Print statistics about used ids.
    """
    if spriteset_stats[0] > 0:
        # NML uses as many concurrent spritesets as possible to prevent sprite duplication.
        # So, instead of the actual amount, we rather print the biggest unsplittable block, since that is what matters.
        generic.print_info(
            "Concurrent spritesets: {}/{} ({})".format(
                spriteset_stats[0], max_sprite_block_size, str(spriteset_stats[1])
            )
        )


"""
The collection which was previoulsy used. add_to_action1 will try to reuse this
collection as long as possible to reduce the duplication of sprites. As soon
as a spriteset with a different feature or amount of sprites is added a new
collection will be created.
"""
last_spriteset_collection = None


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

    setsize = len(real_sprite.parse_sprite_data(spritesets[0]))
    for spriteset in spritesets:
        if setsize != len(real_sprite.parse_sprite_data(spriteset)):
            raise generic.ScriptError(
                "Using spritesets with different sizes in a single sprite group / layout is not possible", pos
            )

    global spriteset_stats
    if spriteset_stats[0] < len(spritesets):
        spriteset_stats = (len(spritesets), pos)

    global last_spriteset_collection
    actions = []
    if last_spriteset_collection is None or not last_spriteset_collection.can_add(spritesets, feature):
        last_spriteset_collection = SpritesetCollection(feature, len(real_sprite.parse_sprite_data(spritesets[0])))
        actions.append(last_spriteset_collection)

    last_spriteset_collection.add(spritesets)

    return actions


def get_action1_index(spriteset):
    """
    Get the index of a spriteset in the action1. The given spriteset must have
    been added in the last call to #add_to_action1. Any new calls to
    #add_to_action1 may or may not allocate a new spriteset collection and as
    such make previous spritesets inaccessible.

    @param spriteset: The spriteset to get the index of.
    @type spriteset: L{SpriteSet}.

    @return: The index in the action1 of the given spriteset.
    @rtype: C{int}
    """
    assert last_spriteset_collection is not None
    return last_spriteset_collection.get_index(spriteset)


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
    global last_spriteset_collection
    if last_spriteset_collection is not None and last_spriteset_collection.feature == feature:
        actions = []
    else:
        last_spriteset_collection = None
        actions = [Action1(feature, 1, 0)]
    return (actions, 0)  # Index is currently always 0, but will change with ext. A1
