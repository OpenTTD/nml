from nml.actions.sprite_count import SpriteCountAction

class SpriteCount(object):
    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite count'

    def get_action_list(self):
        return [SpriteCountAction()]
