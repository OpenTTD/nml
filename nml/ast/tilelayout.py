from nml import generic, expression, global_constants
from nml.actions import action0properties


class TileLayout(object):
    """
    'tile_layout' AST node. A TileLayout is a list of x,y-offset/tileID pairs.
    The x and y offsets are from the northernmost tile of the industry/airport.
    Additionally some extra properties can be stored in the TileLayout, like
    the orientation of the airport.

    @ivar name: The name of this layout by which it can be referenced later.
    @type name: C{str}

    @ivar tile_prop_list: List of offset/tileID and properties.
    @type tile_prop_list: C{list} of L{LayoutTile} and L{LayoutProp}

    @ivar pos: Position information of the 'town_names' block.
    @type pos: L{Position}

    @ivar tile_list: List of tile-offsets/tileIDs.
    @type tile_list: C{list} of C{dict} with properties x, y and tile.

    @ivar properties: table of all properties. Unknown property names are accepted and ignored.
    @type properties: C{dict} with C{str} keys and L{ConstantNumeric} values
    """
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

    def __str__(self):
        ret = 'tilelayout %s {\n' % self.name
        for tile in self.tile_list:
            ret += '\t%s, %s: %s;\n' % (tile['x'], tile['y'], tile['tile'])
        ret += '}\n'
        return ret

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
                tile_id = global_constants.item_names[tile['tile'].value].id
                if not isinstance(tile_id, expression.ConstantNumeric):
                    raise generic.ScriptError("Tile '%s' cannot be used in a tilelayout, as its ID is not a constant." % tile['tile'].value, tile['tile'].pos)
                file.print_wordx(tile_id.value)
            file.newline()
        file.print_bytex(0)
        file.print_bytex(0x80)
        file.newline()


class LayoutTile(object):
    """
    Single tile that is part of a L{TileLayout}.

    @ivar x: X-offset from the northernmost tile of the industry/airport.
    @type x: L{Expression}

    @ivar y: Y-offset from the northernmost tile of the industry/airport.
    @type y: L{Expression}

    @ivar tiletype: TileID of the tile to draw on the given offset.
    @type tiletype: L{Expression}
    """
    def __init__(self, x, y, tiletype):
        self.x = x
        self.y = y
        self.tiletype = tiletype

class LayoutProp(object):
    """
    Property of a L{TileLayout}.

    @ivar name: Name of the property.
    @type name: L{Identifier}

    @iver value: Value of the property.
    @type value: L{Expression}
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value

