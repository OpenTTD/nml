from nml.actions import base_action, real_sprite

class ActionA(base_action.BaseAction):
    """
    Action class for Action A (sprite replacement)

    @ivar sets: List of sprite collections to be replaced
    @type sets: C{list} of (C{int}, L{ConstantNumeric})-tuples
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
            first.write(file, 2)
        file.newline()
        file.end_sprite()

def parse_actionA(replaces):
    """
    Parse replace-block to ActionA.

    @param replaces: Replace-block to parse.
    @type  replaces: L{ReplaceSprite}
    """
    real_sprite_list = real_sprite.parse_sprite_list(replaces.sprite_list, replaces.pcx)

    return [ActionA([(len(real_sprite_list), replaces.start_id)])] + real_sprite_list
