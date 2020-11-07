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

from nml import generic


class SpriteContainer:
    """
    Base class for all AST Nodes that contain real sprites
    Note that this does not inherit from BaseStatement,
    to (amongst other things) avoid various multiple inheritance issues with Spritesets

    @ivar block_type: Type of block (e.g. 'spriteset' ,'replace')
    @type block_type: C{str}

    @ivar block_name: Block-specific name
    @type block_name: L{Identifier}, or C{None} if N/A

    @ivar sprite_data: Mapping of (zoom level, bit-depth) to (sprite list, default file)
    @type sprite_data: C{dict} that maps (C{tuple} of (C{int}, C{int}))
                       to (C{tuple} of (C{list} of (L{RealSprite}, L{RecolourSprite} or L{TemplateUsage}),
                                        L{StringLiteral} or C{None},
                                        L{Position}))
    """

    sprite_blocks = {}

    def __init__(self, block_type, block_name):
        self.block_type = block_type
        self.block_name = block_name
        self.sprite_data = {}
        if block_name is not None:
            if block_name.value in SpriteContainer.sprite_blocks:
                raise generic.ScriptError(
                    "Block with name '{}' is already defined.".format(block_name.value), block_name.pos
                )
            SpriteContainer.sprite_blocks[block_name.value] = self

    def add_sprite_data(self, sprite_list, default_file, pos, zoom_level=0, bit_depth=8, default_mask_file=None):
        assert zoom_level in range(0, 6)
        assert bit_depth in (8, 32)
        key = (zoom_level, bit_depth)
        if key in self.sprite_data:
            msg = (
                "Sprites are already defined for {} '{}' for this zoom "
                + "level / bit depth combination. This data will be overridden."
            )
            msg = msg.format(self.block_type, self.block_name.value)
            generic.print_warning(msg, pos)
        self.sprite_data[key] = (sprite_list, default_file, default_mask_file, pos)

    def get_all_sprite_data(self):
        """
        Get all sprite data.
        Sorting makes sure that the order is consistent, and that the normal zoom, 8bpp sprites appear first.

        @return: List of 6-tuples (sprite_list, default_file, default_mask_file, position, zoom_level, bit_depth).
        @rtype:  C{list} of C{tuple} of (C{list} of (L{RealSprite},
                                         L{RecolourSprite} or L{TemplateUsage}),
                                         L{StringLiteral} or C{None},
                                         L{Position},
                                         C{int},
                                         C{int})
        """
        return [val + key for key, val in sorted(self.sprite_data.items())]

    @classmethod
    def resolve_sprite_block(cls, block_name):
        if block_name.value in cls.sprite_blocks:
            return cls.sprite_blocks[block_name.value]
        raise generic.ScriptError(
            "Undeclared block identifier '{}' encountered".format(block_name.value), block_name.pos
        )
