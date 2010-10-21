from nml import generic, expression
from nml.actions import base_action, action2real, action2layout, real_sprite

class Action1(base_action.BaseAction):
    def __init__(self, feature, num_sets, num_ent):
        self.feature = feature
        self.num_sets = num_sets
        self.num_ent = num_ent

    def write(self, file):
        #<Sprite-number> * <Length> 01 <feature> <num-sets> <num-ent>
        file.start_sprite(6)
        file.print_bytex(1)
        self.feature.write(file, 1)
        file.print_byte(self.num_sets)
        file.print_varx(self.num_ent, 3)
        file.newline()
        file.end_sprite()

class SpriteSet(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (1 <= len(param_list) <= 2):
            raise generic.ScriptError("Spriteset requires 1 or 2 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        if not isinstance(self.name, expression.Identifier):
            raise generic.ScriptError("Spriteset parameter 1 'name' should be an identifier", self.name.pos)
        if len(param_list) >= 2:
            self.pcx = param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("Spriteset-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos
        register_spriteset(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite set:', self.name.value
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

class SpriteGroup(object):
    def __init__(self, name, spriteview_list, pos = None):
        self.name = name
        self.spriteview_list = spriteview_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite group:', self.name.value
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

class LayoutSpriteGroup(object):
    def __init__(self, name, layout_sprite_list, pos = None):
        self.name = name
        self.layout_sprite_list = layout_sprite_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite group:', self.name.value
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 2)

#vehicles, stations, canals, cargos, airports, railtypes, houses, industry tiles, airport tiles, objects
action1_features = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10, 0x07, 0x09, 0x11, 0x0F]

def parse_sprite_block(sprite_block):
    global action1_features
    action_list = []
    action_list_append = []
    spritesets = {} #map names to action1 entries
    num_sets = 0
    num_ent = -1

    if sprite_block.feature.value not in action1_features:
        raise generic.ScriptError("Sprite blocks are not supported for this feature: 0x" + generic.to_hex(sprite_block.feature.value, 2), sprite_block.feature.pos)

    for item in sprite_block.spriteset_list:
        if isinstance(item, SpriteSet):
            real_sprite_list = real_sprite.parse_sprite_list(item.sprite_list, item.pcx)
            action_list.extend(real_sprite_list)
            spritesets[item.name.value] = num_sets
            num_sets += 1

            if num_ent == -1:
                num_ent = len(real_sprite_list)
            elif num_ent != len(real_sprite_list):
                raise generic.ScriptError("All sprite sets in a spriteblock should contain the same number of sprites. Expected " + str(num_ent) + ", got " + str(len(item.sprite_list)), item.pos)

        elif isinstance(item, SpriteGroup):
            action_list_append.extend(action2real.get_real_action2s(item, sprite_block.feature.value, spritesets))
        else:
            assert isinstance(item, LayoutSpriteGroup)
            action_list_append.extend(action2layout.get_layout_action2s(item, sprite_block.feature.value, spritesets))

    if num_sets > 0: action_list.insert(0, Action1(sprite_block.feature, num_sets, num_ent))
    action_list.extend(action_list_append)
    return action_list

#list of sprite sets
spriteset_list = {}

def register_spriteset(spriteset):
    """
    Register a sprite set, so it can be resolved by name later

    @param spriteset: Spriteset to register
    @type spriteset: L{SpriteSet}
    """
    name = spriteset.name.value
    if name in spriteset_list:
        raise generic.ScriptError("Sprite set with name '%s' has already been defined" % name, spriteset.pos)
    spriteset_list[name] = spriteset

def resolve_spriteset(name):
    """
    Resolve a sprite set with a given name

    @param name: Name of the sprite set.
    @type name: L{Identifier}
    
    @return: The sprite set that the name refers to.
    """
    if name.value not in spriteset_list:
        raise generic.ScriptError("Referring to unknown spriteset '%s'" % name.value, name.pos)
    return spriteset_list[name.value]
    