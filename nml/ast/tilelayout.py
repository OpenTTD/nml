from nml import generic, expression, global_constants
from nml.actions import actionB, action0properties


class TileLayout(object):
    def __init__(self, name, tile_list, pos):
        self.name = name.value
        self.tile_prop_list = tile_list
        self.pos = pos
        self.tile_list = []
        self.properties = {}

    def pre_process(self):
        for tileprop in self.tile_prop_list:
            if isinstance(tileprop, LayoutProp):
                name = tileprop.name.value
                if name in self.properties:
                    raise generic.ScriptError("Duplicate property %s in tile layout" % name, tileprop.name.pos)
                self.properties[name] = tileprop.value.reduce_constant(global_constants.const_list)
            else:
                assert isinstance(tileprop, LayoutTile)
                x = tileprop.x.reduce_constant().value
                y = tileprop.y.reduce_constant().value
                tile = tileprop.tiletype.reduce(unknown_id_fatal = False)
                if isinstance(tile, expression.Identifier) and tile.value == 'clear':
                    tile = expression.ConstantNumeric(0xFF)
                self.tile_list.append({'x': x, 'y': y, 'tile': tile})
        assert self.name not in action0properties.tilelayout_names
        action0properties.tilelayout_names[self.name] = self

    def debug_print(self, indentation):
        print indentation*' ' + 'TileLayout'
        for tile in self.tile_list:
            print (indentation+2)*' ' + 'At %d,%d:' % (tile['x'], tile['y'])
            tile['tile'].debug_print(indentation + 4)

    def get_action_list(self):
        return []

    def get_size(self):
        size = 2
        for tile in self.tile_list:
            size += 3
            if not isinstance(tile['tile'], expression.ConstantNumeric):
                size += 2
        return size

    def write(self, file):
        for tile in self.tile_list:
            file.print_bytex(tile['x'])
            file.print_bytex(tile['y'])
            if isinstance(tile['tile'], expression.ConstantNumeric):
                file.print_bytex(tile['tile'].value)
            else:
                if not isinstance(tile['tile'], expression.Identifier):
                    raise generic.ScriptError("Invalid expression type for layout tile", tile['tile'].pos)
                if tile['tile'].value not in global_constants.item_names:
                    raise generic.ScriptError("Unknown tile name", tile['tile'].pos)
                file.print_bytex(0xFE)
                file.print_wordx(global_constants.item_names[tile['tile'].value])
            file.newline()
        file.print_bytex(0)
        file.print_bytex(0x80)
        file.newline()


class LayoutTile(object):
    def __init__(self, x, y, tiletype):
        self.x = x
        self.y = y
        self.tiletype = tiletype

class LayoutProp(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

