from nml import expression, generic, global_constants, unit
from nml.ast import conditional, loop, general
from nml.actions import action0, action2, action3

def validate_item_block(block_list):
    for block in block_list:
        if isinstance(block, PropertyBlock): continue
        if isinstance(block, GraphicsBlock): continue
        if isinstance(block, LiveryOverride): continue
        if isinstance(block, conditional.Conditional):
            while block is not None:
                validate_item_block(block.block)
                block = block.else_block
            continue
        if isinstance(block, loop.Loop):
            validate_item_block(block.body)
            continue
        raise generic.ScriptError("Invalid block type inside 'Item'-block", block.pos)

item_feature = None
item_id = None

class Item(object):
    def __init__(self, params, body, pos):
        self.pos = pos
        if len(params) >= 1:
            self.feature = general.parse_feature(params[0])
        else:
            raise generic.ScriptError("Item block requires at least one parameter, got 0", self.pos)
        if len(params) > 3:
            raise generic.ScriptError("Item block requires at most 3 parameters, found %d" % len(params), self.pos)

        if len(params) == 3:
            self.id = params[2].reduce_constant()
        else:
            self.id = None

        if len(params) >= 2:
            self.name = params[1]
            if not isinstance(self.name, expression.Identifier):
                raise generic.ScriptError("Item parameter 2 'name' should be an identifier", self.pos)
            if self.name.value in global_constants.item_names:
                id = expression.ConstantNumeric(global_constants.item_names[self.name.value])
                if self.id is not None and id.value != self.id.value:
                    raise generic.ScriptError("Item with name '%s' has already been assigned to id %d, cannot reassign to id %d" % (self.name.value, self.id.value, id.value), self.pos)
                self.id = id
        else:
            self.name = None

        if self.id is None:
            self.id = expression.ConstantNumeric(action0.get_free_id(self.feature.value))
        if self.name is not None:
            global_constants.item_names[self.name.value] = self.id.value

        self.body = body
        validate_item_block(body)

    def pre_process(self):
        global item_feature, item_id
        item_id = self.id
        item_feature = self.feature.value
        for b in self.body:
            b.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'Item, feature', hex(self.feature.value)
        for b in self.body: b.debug_print(indentation + 2)

    def get_action_list(self):
        global item_feature, item_id
        item_id = self.id
        item_feature = self.feature.value
        action_list = []
        for b in self.body:
            action_list.extend(b.get_action_list())
        return action_list

    def __str__(self):
        ret = 'item(%d' % self.feature.value
        if self.name is not None:
            ret += ', %s, %s' % (str(self.name), str(self.id))
        ret += ') {\n'
        for b in self.body:
            ret += '\t' + str(b).replace('\n', '\n\t')[0:-1]
        ret += '}\n'
        return ret

class Unit(object):
    def __init__(self, name):
        assert name in unit.units
        self.name = name
        self.type = unit.units[name]['type']
        self.convert = unit.units[name]['convert']

    def __str__(self):
        return self.name

class Property(object):
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

class PropertyBlock(object):
    def __init__(self, prop_list, pos):
        self.prop_list = prop_list
        self.pos = pos

    def pre_process(self):
        for prop in self.prop_list:
            prop.pre_process()

    def debug_print(self, indentation):
        print indentation*' ' + 'Property block:'
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)

    def get_action_list(self):
        global item_feature, item_id
        return action0.parse_property_block(self.prop_list, item_feature, item_id)

    def __str__(self):
        ret = 'property {\n'
        for prop in self.prop_list:
            ret += '%s\n' % str(prop)
        ret += '}\n'
        return ret

class LiveryOverride(object):
    def __init__(self, wagon_id, graphics_block, pos):
        self.graphics_block = graphics_block
        self.wagon_id = wagon_id
        self.pos = pos

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
        global item_feature
        wagon_id = self.wagon_id.reduce_constant([global_constants.item_names])
        return action3.parse_graphics_block(self.graphics_block.graphics_list, self.graphics_block.default_graphics, item_feature, wagon_id, True)

graphics_base_class = action2.make_sprite_group_class(action2.SpriteGroupRefType.SPRITEGROUP, action2.SpriteGroupRefType.SPRITEGROUP, action2.SpriteGroupRefType.NONE, True)

class GraphicsBlock(graphics_base_class):
    def __init__(self, graphics_list, default_graphics):
        self.graphics_list = graphics_list
        self.default_graphics = default_graphics

    def pre_process(self):
        global item_feature
        # initialize base class and pre_process it as well (in that order)
        self.initialize(None, expression.ConstantNumeric(item_feature))
        graphics_base_class.pre_process(self)

    def collect_references(self):
        all_refs = []
        for gfx in [g.action2_id for g in self.graphics_list] + [self.default_graphics]:
            if isinstance(gfx, expression.Identifier):
                all_refs.append(gfx)
        return all_refs

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)
        print (indentation+2)*' ' + 'Default graphics:', self.default_graphics

    def get_action_list(self):
        global item_feature, item_id
        if self.prepare_output():
            return action3.parse_graphics_block(self.graphics_list, self.default_graphics, item_feature, item_id)
        return []

class GraphicsDefinition(object):
    def __init__(self, cargo_id, action2_id):
        self.cargo_id = cargo_id
        self.action2_id = action2_id

    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics:'
        print (indentation+2)*' ' + 'Cargo:', self.cargo_id.value
        print (indentation+2)*' ' + 'Linked to action2:', self.action2_id.value
