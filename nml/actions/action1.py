from nml import generic
from nml.actions import base_action, real_sprite

class Action1(base_action.BaseAction):
    """
    Class representing an Action1

    @ivar feature: Feature of this action1
    @type feature: L{int}

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
        #<Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
        file.start_sprite(6)
        file.print_bytex(1)
        file.print_bytex(self.feature)
        file.print_byte(self.num_sets)
        file.print_varx(self.num_ent, 3)
        file.newline()
        file.end_sprite()

class SpritesetCollection(object):
    def __init__(self, feature, num_sprites_per_spriteset):
        self.feature = feature
        self.num_sprites_per_spriteset = num_sprites_per_spriteset
        self.spritesets = {}

    def can_add(self, spritesets, feature):
        if feature != self.feature:
            return False
        for spriteset in spritesets:
            if len(real_sprite.parse_sprite_list(spriteset.sprite_list, spriteset.pcx)) != self.num_sprites_per_spriteset:
                return False
        return True

    def add(self, spritesets):
        assert self.can_add(spritesets, self.feature)
        for spriteset in spritesets:
            if spriteset not in self.spritesets:
                self.spritesets[spriteset] = len(self.spritesets)

    def get_index(self, spriteset):
        assert spriteset in self.spritesets
        return self.spritesets[spriteset]

    def get_action_list(self):
        actions = [Action1(self.feature, len(self.spritesets), self.num_sprites_per_spriteset)]
        for idx in range(len(self.spritesets)):
            for spriteset, spriteset_offset in self.spritesets.iteritems():
                if idx == spriteset_offset:
                    actions.extend(real_sprite.parse_sprite_list(spriteset.sprite_list, spriteset.pcx, block_name = spriteset.name))
                    break
        return actions
        

last_spriteset_collection = None

def add_to_action1(spritesets, feature):
    if not spritesets:
        return []

    global last_spriteset_collection
    actions = []
    if last_spriteset_collection is None or not last_spriteset_collection.can_add(spritesets, feature):
        last_spriteset_collection = SpritesetCollection(feature, len(real_sprite.parse_sprite_list(spritesets[0].sprite_list, spritesets[0].pcx)))
        actions.append(last_spriteset_collection)

    last_spriteset_collection.add(spritesets)

    return actions

def get_action1_index(spriteset):
    assert last_spriteset_collection is not None
    return last_spriteset_collection.get_index(spriteset)
