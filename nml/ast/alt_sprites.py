from nml import expression, generic

class AltSpritesBlock(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("alternative_sprites-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.name = param_list[0]
        self.zoom_level = param_list[1]
        if len(param_list) >= 3:
            self.pcx = param_list[2].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("alternative_sprites-block parameter 3 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos
        self.name = None

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Alternative sprites'
        print (indentation+2)*' ' + 'Replacement for sprite:', str(self.name)
        print (indentation+2)*' ' + 'Zoom level:', str(self.zoom_level)
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []
