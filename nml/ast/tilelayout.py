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

from nml import expression, generic, global_constants
from nml.actions import action0properties
from nml.ast import assignment, base_statement


class TileLayout(base_statement.BaseStatement):
    """
    'tile_layout' AST node. A TileLayout is a list of x,y-offset/tileID pairs.
    The x and y offsets are from the northernmost tile of the industry/airport.
    Additionally some extra properties can be stored in the TileLayout, like
    the orientation of the airport.

    @ivar name: The name of this layout by which it can be referenced later.
    @type name: C{str}

    @ivar tile_prop_list: List of offset/tileID and properties.
    @type tile_prop_list: C{list} of L{LayoutTile} and L{Assignment}

    @ivar tile_list: List of tile-offsets/tileIDs.
    @type tile_list: C{list} of C{LayoutTile} with constant x and y values.

    @ivar properties: table of all properties. Unknown property names are accepted and ignored.
    @type properties: C{dict} with C{str} keys and L{ConstantNumeric} values
    """

    def __init__(self, name, tile_list, pos):
        base_statement.BaseStatement.__init__(self, "tile layout", pos, False, False)
        self.name = name.value
        self.tile_prop_list = tile_list
        self.tile_list = []
        self.properties = {}

    def pre_process(self):
        for tileprop in self.tile_prop_list:
            if isinstance(tileprop, assignment.Assignment):
                name = tileprop.name.value
                if name in self.properties:
                    raise generic.ScriptError("Duplicate property {} in tile layout".format(name), tileprop.name.pos)
                self.properties[name] = tileprop.value.reduce_constant(global_constants.const_list)
            else:
                assert isinstance(tileprop, LayoutTile)
                x = tileprop.x.reduce_constant()
                y = tileprop.y.reduce_constant()
                tile = tileprop.tiletype.reduce(unknown_id_fatal=False)
                if isinstance(tile, expression.Identifier) and tile.value == "clear":
                    tile = expression.ConstantNumeric(0xFF)
                self.tile_list.append(LayoutTile(x, y, tile))
        if self.name in action0properties.tilelayout_names:
            raise generic.ScriptError(
                "A tile layout with name '{}' has already been defined.".format(self.name), self.pos
            )
        action0properties.tilelayout_names[self.name] = self

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "TileLayout")
        for tile in self.tile_list:
            generic.print_dbg(indentation + 2, "At {:d},{:d}:".format(tile.x, tile.y))
            tile.tiletype.debug_print(indentation + 4)

    def get_action_list(self):
        return []

    def __str__(self):
        return "tilelayout {} {{\n\t{}\n}}\n".format(self.name, "\n\t".join(str(x) for x in self.tile_prop_list))

    def get_size(self):
        size = 2
        for tile in self.tile_list:
            size += 3
            if not isinstance(tile.tiletype, expression.ConstantNumeric):
                size += 2
        return size

    def write(self, file):
        for tile in self.tile_list:
            file.print_bytex(tile.x.value)
            file.print_bytex(tile.y.value)
            if isinstance(tile.tiletype, expression.ConstantNumeric):
                file.print_bytex(tile.tiletype.value)
            else:
                if not isinstance(tile.tiletype, expression.Identifier):
                    raise generic.ScriptError("Invalid expression type for layout tile", tile.tiletype.pos)
                if tile.tiletype.value not in global_constants.item_names:
                    raise generic.ScriptError("Unknown tile name", tile.tiletype.pos)
                file.print_bytex(0xFE)
                tile_id = global_constants.item_names[tile.tiletype.value].id
                if not isinstance(tile_id, expression.ConstantNumeric):
                    raise generic.ScriptError(
                        "Tile '{}' cannot be used in a tilelayout, as its ID is not a constant.".format(
                            tile.tiletype.value
                        ),
                        tile.tiletype.pos,
                    )
                file.print_wordx(tile_id.value)
            file.newline()
        file.print_bytex(0)
        file.print_bytex(0x80)
        file.newline()


class LayoutTile:
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

    def __str__(self):
        return "{}, {}: {};".format(self.x, self.y, self.tiletype)
