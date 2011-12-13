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

from nml import expression, generic, global_constants, unit
from nml.ast import base_statement, general
from nml.actions import action0, action2, action2var, action3

item_feature = None
item_id = None

class Item(base_statement.BaseStatementList):
    """
    AST-node representing an item block
    @ivar feature: Feature of the item
    @type feature: L{ConstantNumeric}

    @ivar name: Name of the item
    @type name: L{Identifier} or C{None} if N/A.

    @ivar id: Numeric ID of the item
    @type id: C{int}
    """
    def __init__(self, params, body, pos):
        base_statement.BaseStatementList.__init__(self, "item-block", pos, base_statement.BaseStatementList.LIST_TYPE_ITEM, body)
        if len(params) >= 1:
            self.feature = general.parse_feature(params[0])
        else:
            raise generic.ScriptError("Item block requires at least one parameter, got 0", self.pos)
        if len(params) > 3:
            raise generic.ScriptError("Item block requires at most 3 parameters, found %d" % len(params), self.pos)

        self.id = params[2] if len(params) == 3 else None
        self.name = params[1] if len(params) >= 2 else None

    def register_names(self):
        if self.id:
            self.id = self.id.reduce(global_constants.const_list)
        if self.name:
            if not isinstance(self.name, expression.Identifier):
                raise generic.ScriptError("Item parameter 2 'name' should be an identifier", self.pos)
            if self.name.value in global_constants.item_names:
                existing_id = global_constants.item_names[self.name.value].id
                if not isinstance(existing_id, expression.ConstantNumeric):
                    raise generic.ScriptError("Item with name '%s' has already been assigned a non-constant ID, extending this item definition is not possible." % self.name.value, self.pos)
                if self.id is not None and (not isinstance(self.id, expression.ConstantNumeric) or existing_id.value != self.id.value):
                    raise generic.ScriptError("Item with name '%s' has already been assigned to id %d, cannot reassign to id %d" % (self.name.value, existing_id.value, self.id.value), self.pos)
                self.id = existing_id

        if self.id is None:
            self.id = expression.ConstantNumeric(action0.get_free_id(self.feature.value))
        if self.name is not None:
            global_constants.item_names[self.name.value] = self
        base_statement.BaseStatementList.register_names(self)

    def pre_process(self):
        global item_feature, item_id
        item_id = self.id
        item_feature = self.feature.value
        base_statement.BaseStatementList.pre_process(self)

    def debug_print(self, indentation):
        print indentation*' ' + 'Item, feature', hex(self.feature.value)
        base_statement.BaseStatementList.debug_print(self, indentation + 2)

    def get_action_list(self):
        global item_feature, item_id
        item_id = self.id
        item_feature = self.feature.value
        return base_statement.BaseStatementList.get_action_list(self)

    def __str__(self):
        ret = 'item(%d' % self.feature.value
        if self.name is not None:
            ret += ', %s' % str(self.name)
        if self.id is not None:
            ret += ', %s' % str(self.id)
        ret += ') {\n'
        ret += base_statement.BaseStatementList.__str__(self)
        ret += '}\n'
        return ret

class Unit(object):
    def __init__(self, name):
        assert name in unit.units
        self.name = name
        self.type = unit.units[name]['type']
        self.convert = unit.units[name]['convert']
        self.ottd_mul = unit.units[name]['ottd_mul']
        self.ottd_shift = unit.units[name]['ottd_shift']

    def __str__(self):
        return self.name

class Property(object):
    """
    AST-node representing a single property. These are only valid
    insde a PropertyBlock.

    @ivar name: The name (or number) of this property.
    @type name: L{Identifier} or L{ConstantNumeric}.

    @ivar value: The value that will be assigned to this property.
    @type value: L{Expression}.

    @ivar unit: The unit of the value.
    @type unit: L{Unit}

    @ivar pos: Position information.
    @type pos: L{Position}
    """
    def __init__(self, name, value, unit, pos):
        self.pos = pos
        self.name = name
        self.value = value
        self.unit = unit

    def pre_process(self):
        self.value = self.value.reduce(global_constants.const_list, unknown_id_fatal = False)
        if self.unit is not None and not (isinstance(self.value, expression.ConstantNumeric) or isinstance(self.value, expression.ConstantFloat)):
            raise generic.ScriptError("Using a unit for a property is only allowed if the value is constant", self.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'Property:', self.name.value
        self.value.debug_print(indentation + 2)

    def __str__(self):
        unit = '' if self.unit is None else ' ' + str(self.unit)
        return '\t%s: %s%s;' % (self.name, self.value, unit)

class PropertyBlock(base_statement.BaseStatement):
    """
    Block that contains a list of property/value pairs to be assigned
    to the current item.

    @ivar prop_list: List of properties.
    @type prop_list: C{list} of L{Property}
    """
    def __init__(self, prop_list, pos):
        base_statement.BaseStatement.__init__(self, "property-block", pos, in_item = True, out_item = False)
        self.prop_list = prop_list

    def pre_process(self):
        for prop in self.prop_list:
            prop.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'Property block:'
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)

    def get_action_list(self):
        return action0.parse_property_block(self.prop_list, item_feature, item_id)

    def __str__(self):
        ret = 'property {\n'
        for prop in self.prop_list:
            ret += '%s\n' % str(prop)
        ret += '}\n'
        return ret

class LiveryOverride(base_statement.BaseStatement):
    def __init__(self, wagon_id, graphics_block, pos):
        base_statement.BaseStatement.__init__(self, "livery override", pos, in_item = True, out_item = False)
        self.graphics_block = graphics_block
        self.wagon_id = wagon_id

    def pre_process(self):
        self.graphics_block.pre_process()
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Liverry override, wagon id:'
        self.wagon_id.debug_print(indentation + 2)
        for graphics in self.graphics_block.graphics_list:
            graphics.debug_print(indentation + 2)
        print (indentation+2)*' ' + 'Default graphics:', self.graphics_block.default_graphics

    def get_action_list(self):
        wagon_id = self.wagon_id.reduce_constant([(global_constants.item_names, global_constants.item_to_id)])
        return action3.parse_graphics_block(self.graphics_block, item_feature, wagon_id, True)

    def __str__(self):
        ret = 'livery_override(%s) {\n' % str(self.wagon_id)
        for graphics in self.graphics_block.graphics_list:
            ret += "\t%s\n" % str(graphics)
        if self.graphics_block.default_graphics is not None: ret += '\t%s;\n' % str(self.graphics_block.default_graphics)
        ret += '}\n'
        return ret

graphics_base_class = action2.make_sprite_group_class(False, False, True)

class GraphicsBlock(graphics_base_class):
    def __init__(self, graphics_list, default_graphics, pos):
        base_statement.BaseStatement.__init__(self, "graphics-block", pos, in_item = True, out_item = False)
        self.graphics_list = graphics_list
        self.default_graphics = default_graphics

    def pre_process(self):
        for graphics_def in self.graphics_list:
            graphics_def.reduce_expressions(item_feature)
        if self.default_graphics is not None:
            self.default_graphics = action2var.reduce_varaction2_expr(self.default_graphics, item_feature)

        # initialize base class and pre_process it as well (in that order)
        self.initialize(None, item_feature)
        graphics_base_class.pre_process(self)

    def collect_references(self):
        all_refs = []
        for result in [g.result for g in self.graphics_list] + [self.default_graphics]:
            if isinstance(result, expression.SpriteGroupRef): # Default may be None
                all_refs.append(result)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
        if self.default_graphics is not None:
            print (indentation+2)*' ' + 'Default graphics:'
            self.default_graphics.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_output():
            return action3.parse_graphics_block(self, item_feature, item_id)
        return []

    def __str__(self):
        ret = 'graphics {\n'
        for graphics in self.graphics_list:
            ret += "\t%s\n" % str(graphics)
        if self.default_graphics is not None: ret += '\t%s;\n' % str(self.default_graphics)
        ret += '}\n'
        return ret

class GraphicsDefinition(object):
    def __init__(self, cargo_id, result, unit = None):
        self.cargo_id = cargo_id
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_feature):
        # Do not reduce cargo-id (yet)
        if self.result is None:
            raise generic.ScriptError("Returning the computed value is not possible in a graphics-block, as there is no computed value.", self.cargo_id.pos)
        self.result = action2var.reduce_varaction2_expr(self.result, var_feature)

    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo ID:'
        self.cargo_id.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if self.result is not None:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.cargo_id)
        if self.result is None:
            ret += ': return;'
        elif isinstance(self.result, expression.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret

