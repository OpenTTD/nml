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
item_size = None

class Item(base_statement.BaseStatementList):
    """
    AST-node representing an item block
    @ivar feature: Feature of the item
    @type feature: L{ConstantNumeric}

    @ivar name: Name of the item
    @type name: L{Identifier} or C{None} if N/A.

    @ivar id: Numeric ID of the item
    @type id: L{ConstantNumeric} or C{None} if N/A

    @ivar size: Size, used by houses only
    @type size: L{ConstantNumeric} or C{None} if N/A
    """
    def __init__(self, params, body, pos):
        base_statement.BaseStatementList.__init__(self, "item-block", pos, base_statement.BaseStatementList.LIST_TYPE_ITEM, body)

        if not (1 <= len(params) <= 4):
            raise generic.ScriptError("Item block requires between 1 and 4 parameters, found {:d}.".format(len(params)), self.pos)
        self.feature = general.parse_feature(params[0])
        if self.feature.value in (0x08, 0x0C, 0x0E):
            raise generic.ScriptError("Defining item blocks for this feature is not allowed.", self.pos)
        self.name = params[1] if len(params) >= 2 else None

        self.id = params[2].reduce_constant(global_constants.const_list) if len(params) >= 3 else None
        if isinstance(self.id, expression.ConstantNumeric) and self.id.value == -1:
            self.id = None # id == -1 means default

        if len(params) >= 4:
            if self.feature.value != 0x07:
                raise generic.ScriptError("item-block parameter 4 'size' may only be set for houses", params[3].pos)
            self.size = params[3].reduce_constant(global_constants.const_list)
            if self.size.value not in action0.house_sizes:
                raise generic.ScriptError("item-block parameter 4 'size' does not have a valid value", self.size.pos)
        else:
            self.size = None

    def register_names(self):
        if self.name:
            if not isinstance(self.name, expression.Identifier):
                raise generic.ScriptError("Item parameter 2 'name' should be an identifier", self.pos)
            if self.name.value in global_constants.item_names:
                existing_id = global_constants.item_names[self.name.value].id
                if self.id is not None and existing_id.value != self.id.value:
                    raise generic.ScriptError("Duplicate item with name '{}'. This item has already been assigned to id {:d}, cannot reassign to id {:d}".format(self.name.value, existing_id.value, self.id.value), self.pos)
                self.id = existing_id

        # We may have to reserve multiple item IDs for houses
        num_ids = action0.house_sizes[self.size.value] if self.size is not None else 1
        if self.id is None:
            self.id = expression.ConstantNumeric(action0.get_free_id(self.feature.value, num_ids, self.pos))
        elif not action0.check_id_range(self.feature.value, self.id.value, num_ids, self.id.pos):
            action0.mark_id_used(self.feature.value, self.id.value, num_ids)
        if self.name is not None:
            global_constants.item_names[self.name.value] = self
        base_statement.BaseStatementList.register_names(self)

    def pre_process(self):
        global item_feature, item_id, item_size
        item_id = self.id
        item_feature = self.feature.value
        item_size = self.size
        base_statement.BaseStatementList.pre_process(self)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Item, feature', hex(self.feature.value))
        base_statement.BaseStatementList.debug_print(self, indentation + 2)

    def get_action_list(self):
        global item_feature, item_id, item_size
        item_id = self.id
        item_feature = self.feature.value
        item_size = self.size
        return base_statement.BaseStatementList.get_action_list(self)

    def __str__(self):
        ret = 'item({:d}'.format(self.feature.value)
        if self.name is not None:
            ret += ', {}'.format(self.name)
        ret += ', {}'.format(str(self.id) if self.id is not None else "-1")
        if self.size is not None:
            sizes =["1X1", None, "2X1", "1X2", "2X2"]
            ret += ', HOUSE_SIZE_{}'.format(sizes[self.size.value])
        ret += ') {\n'
        ret += base_statement.BaseStatementList.__str__(self)
        ret += '}\n'
        return ret

class Property:
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

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Property:', self.name.value)
        self.value.debug_print(indentation + 2)

    def __str__(self):
        unit = '' if self.unit is None else ' ' + str(self.unit)
        return '\t{}: {}{};'.format(self.name, self.value, unit)

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
        generic.print_dbg(indentation, 'Property block:')
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)

    def get_action_list(self):
        return action0.parse_property_block(self.prop_list, item_feature, item_id, item_size)

    def __str__(self):
        ret = 'property {\n'
        for prop in self.prop_list:
            ret += '{}\n'.format(prop)
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
        generic.print_dbg(indentation, 'Livery override, wagon id:')
        self.wagon_id.debug_print(indentation + 2)
        for graphics in self.graphics_block.graphics_list:
            graphics.debug_print(indentation + 2)
        generic.print_dbg(indentation + 2, 'Default graphics:', self.graphics_block.default_graphics)

    def get_action_list(self):
        wagon_id = self.wagon_id.reduce_constant([(global_constants.item_names, global_constants.item_to_id)])
        return action3.parse_graphics_block(self.graphics_block, item_feature, wagon_id, item_size, True)

    def __str__(self):
        ret = 'livery_override({}) {{\n'.format(self.wagon_id)
        for graphics in self.graphics_block.graphics_list:
            ret += "\t{}\n".format(graphics)
        if self.graphics_block.default_graphics is not None:
            ret += '\t{}\n'.format(self.graphics_block.default_graphics)
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
            if self.default_graphics.value is None:
                raise generic.ScriptError("Returning the computed value is not possible in a graphics-block, as there is no computed value.", self.pos)
            self.default_graphics.value = action2var.reduce_varaction2_expr(self.default_graphics.value, item_feature)

        # initialize base class and pre_process it as well (in that order)
        self.initialize(None, item_feature)
        graphics_base_class.pre_process(self)

    def collect_references(self):
        all_refs = []
        for result in [g.result for g in self.graphics_list] + ([self.default_graphics] if self.default_graphics is not None else []):
            all_refs += result.value.collect_references()
        return all_refs

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Graphics block:')
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
        if self.default_graphics is not None:
            generic.print_dbg(indentation + 2, 'Default graphics:')
            self.default_graphics.debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_act2_output():
            return action3.parse_graphics_block(self, item_feature, item_id, item_size)
        return []

    def __str__(self):
        ret = 'graphics {\n'
        for graphics in self.graphics_list:
            ret += "\t{}\n".format(graphics)
        if self.default_graphics is not None:
            ret += '\t{}\n'.format(self.default_graphics)
        ret += '}\n'
        return ret

class GraphicsDefinition:
    def __init__(self, cargo_id, result, unit = None):
        self.cargo_id = cargo_id
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_feature):
        # Do not reduce cargo-id (yet)
        if self.result.value is None:
            raise generic.ScriptError("Returning the computed value is not possible in a graphics-block, as there is no computed value.", self.result.pos)
        self.result.value = action2var.reduce_varaction2_expr(self.result.value, var_feature)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Cargo ID:')
        self.cargo_id.debug_print(indentation + 2)
        generic.print_dbg(indentation, 'Result:')
        self.result.debug_print(indentation + 2)

    def __str__(self):
        return '{}: {}'.format(self.cargo_id, self.result)

