from nml import expression, generic
from nml.actions import actionA, action5


class ReplaceSprite(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (1 <= len(param_list) <= 2):
            raise generic.ScriptError("replace-block requires 1 or 2 parameters, encountered " + str(len(param_list)), pos)
        self.start_id = param_list[0].reduce_constant()
        if len(param_list) >= 2:
            self.pcx = param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("replace-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites starting at', self.start_id
        print (indentation+2)*' ' + 'Source:', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return actionA.parse_actionA(self)

class ReplaceNewSprite(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (1 <= len(param_list) <= 3):
            raise generic.ScriptError("replacenew-block requires 1 to 3 parameters, encountered " + str(len(param_list)), pos)
        self.type = param_list[0]
        if len(param_list) >= 2:
            self.pcx = param_list[1].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("replace-block parameter 2 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        if len(param_list) >= 3:
            self.offset = param_list[2]
        else:
            self.offset = expression.ConstantNumeric(0)
        self.sprite_list = sprite_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Replace sprites for new features of type', self.type
        print (indentation+2)*' ' + 'Offset:  ', self.offset
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action5.parse_action5(self)
