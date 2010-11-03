from nml import expression, generic, global_constants
from nml.actions import action1, action2, real_sprite
from nml.ast import general

class SpriteBlock(object):
    def __init__(self, spriteset_list, pos):
        generic.print_warning("Using a spriteblock is deprecated and will not be supported in the future. Place your spriteset(s) and/or spritegroup(s) in the global scope instead.", pos)
        self.spriteset_list = spriteset_list
        self.pos = pos

    def pre_process(self):
        for spriteset in self.spriteset_list:
            spriteset.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite block'
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 2)

    def get_action_list(self):
        action_list = []
        for spriteset in self.spriteset_list:
            action_list.extend(spriteset.get_action_list())
        return action_list

class TemplateDeclaration(object):
    def __init__(self, name, param_list, sprite_list, pos):
        self.name = name
        self.param_list = param_list
        self.sprite_list = sprite_list
        self.pos = pos

    def pre_process(self):
        #check that all templates that are referred to exist at this point
        #This prevents circular dependencies
        for sprite in self.sprite_list:
            if isinstance(sprite, real_sprite.TemplateUsage):
                if sprite.name.value == self.name.value:
                    raise generic.ScriptError("Sprite template '%s' includes itself." % sprite.name.value, self.pos)
                elif sprite.name.value not in real_sprite.sprite_template_map:
                    raise generic.ScriptError("Encountered unknown template identifier: " + sprite.name.value, sprite.pos)
        #Register template
        if self.name.value not in real_sprite.sprite_template_map:
            real_sprite.sprite_template_map[self.name.value] = self
        else:
            raise generic.ScriptError("Template named '%s' is already defined, first definition at %s" % (self.name.value, real_sprite.sprite_template_map[self.name.value].pos), self.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Template declaration:', self.name.value
        print (indentation+2)*' ' + 'Parameters:'
        for param in self.param_list:
            param.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []


class SpriteView(object):
    def __init__(self, name, spriteset_list, pos):
        self.name = name
        self.spriteset_list = spriteset_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite view:', self.name.value
        print (indentation+2)*' ' + 'Sprite sets:'
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 4)

class LayoutSprite(object):
    def __init__(self, type, param_list, pos):
        self.type = type
        self.param_list = param_list
        self.pos = pos

    # called by LayoutSpriteGroup
    def collect_spritesets(self):
        used_sets = []
        for layout_param in self.param_list:
            if isinstance(layout_param.value, expression.Identifier):
                used_sets.append(layout_param.value)
        return used_sets

    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite of type:', self.type
        for layout_param in self.param_list:
            layout_param.debug_print(indentation + 2)

class LayoutParam(object):
    def __init__(self, name, value, pos):
        self.name = name
        self.value = value.reduce(global_constants.const_list, False)
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Layout parameter:', self.name.value
        self.value.debug_print(indentation + 2)
