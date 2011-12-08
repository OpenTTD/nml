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
from nml.actions import action2
from .base_expression import Type, Expression

class SpriteGroupRef(Expression):
    """
    Container for a reference to a sprite group / layout

    @ivar name: Name of the referenced item
    @type name: L{Identifier}

    @ivar param_list: List of parameters to be passed
    @type param_list: C{list} of L{Expression}

    @ivar pos: Position of this reference
    @type pos: L{Position}

    @ivar act2: Action2 that is the target of this reference
                    To be used for action2s that have no direct equivalent in the AST
    @type act2: L{Action2}
    """
    def __init__(self, name, param_list, pos, act2 = None):
        self.name = name
        self.param_list = param_list
        self.pos = pos
        self.act2 = act2

    def debug_print(self, indentation):
        print indentation*' ' +'Reference to: ' + str(self.name)
        if len(self.param_list) != 0:
            print 'Parameters:'
            for p in self.param_list:
                p.debug_print(indentation + 2)

    def __str__(self):
        if self.param_list:
            return '%s(%s)' % (self.name, ', '.join(str(x) for x in self.param_list))
        return str(self.name)

    def get_action2_id(self, feature):
        """
        Get the action2 set-ID that this reference maps to

        @param feature: Feature of the action2
        @type feature: C{int}

        @return: The set ID
        @rtype: C{int}
        """
        if self.act2 is not None: return self.act2.id
        if self.name.value == 'CB_FAILED': return 0 # 0 serves as a failed CB result because it is never used
        try:
            spritegroup = action2.resolve_spritegroup(self.name)
        except generic.ScriptError:
            assert False, "Illegal action2 reference '%s' encountered." % self.name.value

        return spritegroup.get_action2(feature).id

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def type(self):
        return Type.SPRITEGROUP_REF

    def __eq__(self, other):
        return other is not None and isinstance(other, SpriteGroupRef) and other.name == self.name and other.param_list == self.param_list

    def __hash__(self):
        return hash(self.name) ^ hash(tuple(self.param_list))
