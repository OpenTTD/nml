from generic import *
from actions.action0 import *
from actions.action1 import *
from actions.action2var import *
from actions.action7 import *
from actions.action8 import *
from actions.actionB import *
from actions.actionD import *
from actions.actionE import *
import operator

def print_script(script, indent):
    for r in script:
        r.debug_print(indent)

class Operator:
    ADD     = 0
    SUB     = 1
    DIV     = 2
    MOD     = 3
    MUL     = 4
    AND     = 5
    OR      = 6
    XOR     = 7
    VAL2    = 8
    CMP_EQ  = 9
    CMP_NEQ = 10
    CMP_LT  = 11
    CMP_GT  = 12
    MIN     = 13
    MAX     = 14

########### expressions ###########
class Expr:
    def debug_print(self, indentation):
        print indentation*' ' + 'Expression'

class BinOp(Expr):
    def __init__(self, op, expr1, expr2):
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op
        self.expr1.debug_print(indentation + 2)
        self.expr2.debug_print(indentation + 2)

class TernaryOp(Expr):
    def __init__(self, guard, expr1, expr2):
        self.guard = guard
        self.expr1 = expr1
        self.expr2 = expr2
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Ternary operator'
        print indentation*' ' + 'Guard:'
        self.guard.debug_print(indentation + 2)
        print indentation*' ' + 'Expression 1:'
        self.expr1.debug_print(indentation + 2)
        print indentation*' ' + 'Expression 2:'
        self.expr2.debug_print(indentation + 2)

class Assignment:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)

class Parameter(Expr):
    def __init__(self, num):
        self.num = num
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)

class ParameterAssignment:
    def __init__(self, param, value):
        self.param = param
        self.value = reduce_expr(value)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter assignment'
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)
    
    def get_action_list(self):
        return parse_actionD(self)

class Variable:
    def __init__(self, num, shift = None, mask = None, param = None):
        self.num = num
        self.shift = shift if shift != None else ConstantNumeric(0)
        self.mask = mask if mask != None else ConstantNumeric(0xFFFFFFFF)
        self.param = param
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Action2 variable'
        self.num.debug_print(indentation + 2)
        if self.param != None:
            print (indentation+2)*' ' + 'Parameter:'
            if isinstance(self.param, str):
                print (indentation+4)*' ' + 'Procedure call:', self.param
            else:
                self.param.debug_print(indentation + 4)

class String:
    def __init__(self, name, params = []):
        self.name = name
        self.params = params
    def debug_print(self, indentation):
        print indentation*' ' + 'String: ' + self.name
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)

class ConstantNumeric(Expr):
    def __init__(self, value):
        self.value = truncate_int32(value)
    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value
    def write(self, file, size):
        print_varx(file, self.value, size)

# compile-time expression evaluation
compile_time_operator = {
    Operator.ADD:     operator.add,
    Operator.SUB:     operator.sub,
    Operator.DIV:     operator.div,
    Operator.MOD:     operator.mod,
    Operator.MUL:     operator.mul,
    Operator.AND:     operator.and_,
    Operator.OR:      operator.or_,
    Operator.XOR:     operator.xor,
    Operator.VAL2:    lambda a, b: b,
    Operator.CMP_EQ:  operator.eq,
    Operator.CMP_NEQ: operator.ne,
    Operator.CMP_LT:  operator.lt,
    Operator.CMP_GT:  operator.gt,
    Operator.MIN:     lambda a, b: min(a, b),
    Operator.MAX:     lambda a, b: max(a, b)
}

def reduce_expr(expr, id_dicts = []):
    global compile_time_operator
    if isinstance(expr, BinOp):
        expr.expr1 = reduce_expr(expr.expr1, id_dicts)
        expr.expr2 = reduce_expr(expr.expr2, id_dicts)
        if isinstance(expr.expr1, ConstantNumeric) and isinstance(expr.expr2, ConstantNumeric):
            return ConstantNumeric(compile_time_operator[expr.op](expr.expr1.value, expr.expr2.value))
    elif isinstance(expr, Parameter):
        expr.num = reduce_expr(expr.num, id_dicts)
    elif isinstance(expr, Variable):
        expr.num = reduce_expr(expr.num, id_dicts)
        expr.shift = reduce_expr(expr.shift, id_dicts)
        expr.mask = reduce_expr(expr.mask, id_dicts)
        expr.param = reduce_expr(expr.num, id_dicts)
    elif isinstance(expr, str):
        for id_dict in id_dicts:
            try:
                value = id_dict[expr]
                return ConstantNumeric(value)
            except KeyError:
                pass
        raise ScriptError("Unrecognized identifier '" + expr + "' encountered")
    return expr

########### code blocks ###########
class GRF:
    def __init__(self, alist):
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist:
            if not isinstance(assignment.value, String):
                raise ScriptError("Assignments in GRF-block must be constant strings")
            if assignment.name == "name": self.name = assignment.value
            elif assignment.name == "desc": self.desc = assignment.value
            elif assignment.name == "grfid": self.grfid = assignment.value
            else: raise ScriptError("Unkown item in GRF-block: " + assignment.name)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        if self.grfid != None:
            print (2+indentation)*' ' + 'grfid:'
            self.grfid.debug_print(indentation + 4)
        if self.name != None:
            print (2+indentation)*' ' + 'Name:'
            self.name.debug_print(indentation + 4)
        if self.desc != None:
            print (2+indentation)*' ' + 'Description:'
            self.desc.debug_print(indentation + 4)
    
    def get_action_list(self):
        return [Action8(self.grfid, self.name, self.desc)]

class Conditional:
    def __init__(self, expr, block, else_block = None):
        self.expr = expr
        self.block = block
        self.else_block = else_block
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Conditional'
        if self.expr != None:
            print (2+indentation)*' ' + 'Expression:'
            self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        print_script(self.block, indentation + 4)
        if self.else_block != None:
            print (indentation)*' ' + 'Else block:'
            self.else_block.debug_print(indentation)
    
    def get_action_list(self):
        return parse_conditional_block(self)

class Loop:
    def __init__(self, expr, block):
        self.expr = expr
        self.block = block
    
    def debug_print(self, indentation):
        print indentation*' ' + 'While loop'
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Block:'
        print_script(self.block, indentation + 4)
    
    def get_action_list(self):
        return parse_loop_block(self)

class Switch:
    def __init__(self, feature, var_range, name, expr, body):
        self.feature = feature
        self.var_range = var_range
        self.name = name
        self.expr = expr
        self.body = body
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =,',self.feature,', name =', self.name
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)
    
    def get_action_list(self):
        return parse_varaction2(self)

class SwitchBody:
    def __init__(self, default):
        self.default = default
        self.ranges = []
    
    def add_range(self, switch_range):
        self.ranges.append(switch_range)
        return self
    
    def debug_print(self, indentation):
        for r in self.ranges:
            r.debug_print(indentation)
        print indentation*' ' + 'Default:'
        if isinstance(self.default, str):
            print (indentation+2)*' ' + 'Go to switch:', self.default
        else:
            self.default.debug_print(indentation + 2)

class SwitchRange:
    def __init__(self, min, max, result):
        self.min = min
        self.max = max
        self.result = result
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, str):
            print (indentation+2)*' ' + 'Go to switch:', self.result
        else:
            self.result.debug_print(indentation + 2)

class DeactivateBlock:
    def __init__(self, grfid):
        self.grfid = grfid
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Deactivate other newgrf:', hex(self.grfid)
    
    def get_action_list(self):
        return [ActionE(self.grfid)]

def validate_item_block(block_list):
    for block in block_list:
        if isinstance(block, PropertyBlock): continue
        if isinstance(block, GraphicsBlock): continue
        if isinstance(block, Conditional):
            while block != None:
                validate_item_block(block.block)
                block = block.else_block
            continue
        if isinstance(block, Loop):
            validate_item_block(block.body)
            continue
        raise ScriptError("Invalid block type inside 'Item'-block")

item_feature = None
item_id = None

class Item:
    def __init__(self, feature, body, id = None):
        self.feature = feature
        self.body = body
        self.id = id
        validate_item_block(body)
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Item, feature', hex(self.feature)
        for b in self.body: b.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature, item_id
        if self.id != None:
            item_id = self.id
        else:
            item_id = ConstantNumeric(get_free_id(self.feature))
        item_feature = self.feature
        action_list = []
        for b in self.body:
            action_list.extend(b.get_action_list())
        return action_list

class Property:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Property:', self.name
        if isinstance(self.value, str):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)

class PropertyBlock:
    def __init__(self, prop_list):
        self.prop_list = prop_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Property block:'
        for prop in self.prop_list:
            prop.debug_print(indentation + 2)
    
    def get_action_list(self):
        global item_feature, item_id
        return parse_property_block(self.prop_list, item_feature, item_id)

class GraphicsBlock:
    def __init__(self, graphics_list):
        self.graphics_list = graphics_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Graphics block:'
        for graphics in self.graphics_list:
            graphics.debug_print(indentation + 2)

class SpriteBlock:
    def __init__(self, feature, spriteset_list):
        self.feature = feature
        self.spriteset_list = spriteset_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite block, feature', hex(self.feature)
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 2)
    def get_action_list(self):
        return parse_sprite_block(self)

class SpriteSet:
    def __init__(self, name, pcx, sprite_list):
        self.name = name
        self.pcx = pcx
        self.sprite_list = sprite_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite set:', self.name
        print (indentation+2)*' ' + 'Source:  ', self.pcx
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

class RealSprite:
    def __init__(self, xpos, ypos, xsize, ysize, xrel, yrel, compression = 0x01):
        self.xpos = xpos
        self.ypos = ypos
        self.xsize = xsize
        self.ysize = ysize
        self.xrel = xrel
        self.yrel = yrel
        self.compression = compression
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Real sprite'
        print (indentation+2)*' ' + 'position: (', self.xpos,  ',', self.ypos,  ')'
        print (indentation+2)*' ' + 'size:     (', self.xsize, ',', self.ysize, ')'
        print (indentation+2)*' ' + 'offset:   (', self.xrel,  ',', self.yrel,  ')'
        print (indentation+2)*' ' + 'compression: ', self.compression

class SpriteGroup:
    def __init__(self, name, spriteview_list):
        self.name = name
        self.spriteview_list = spriteview_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite group:', self.name
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

class SpriteView:
    def __init__(self, name, spriteset_list):
        self.name = name
        self.spriteset_list = spriteset_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Sprite view:', self.name
        print (indentation+2)*' ' + 'Sprite sets:'
        for spriteset in self.spriteset_list:
            print (indentation+4)*' ' + spriteset

class LayoutSpriteGroup:
    def __init__(self, name, layout_sprite_list):
        self.name = name
        self.layout_sprite_list = layout_sprite_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite group:', self.name
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 2)

class LayoutSprite:
    def __init__(self, type, param_list):
        self.type = type
        self.param_list = param_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Tile layout sprite of type:', self.type
        for layout_param in self.param_list:
            layout_param.debug_print(indentation + 2)

class LayoutParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Layout parameter:', self.name
        if isinstance(self.value, str):
            print (indentation + 2)*' ' + 'String: ', self.value
        else:
            self.value.debug_print(indentation + 2)

class Error:
    def __init__(self, severity, msg, data, param1, param2):
        self.severity = severity
        self.msg = msg
        self.data = data
        self.param1 = param1
        self.param2 = param2
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Error, msg = ', self.msg
        print (indentation+2)*' ' + 'Severity:'
        self.severity.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Data: ', self.data
        print (indentation+2)*' ' + 'Param1: ', self.param1
        print (indentation+2)*' ' + 'Param2: ', self.param2
    
    def get_action_list(self):
        return parse_error_block(self)

class CargoTable:
    def __init__(self, cargo_list):
        self.cargo_list = cargo_list
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Cargo table'
        for cargo in self.cargo_list:
            print (indentation+2)*' ' + 'Cargo:', cargo
    
    def get_action_list(self):
        return get_cargolist_action(self.cargo_list)
