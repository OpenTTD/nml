from generic import *
from actions.action0 import *
from actions.action7 import *
from actions.action8 import *
from actions.actionB import *
from actions.actionD import *
from actions.actionE import *

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
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter assignment'
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)
    
    def get_action_list(self):
        return parse_actionD(self)

class AssignmentList:
    def __init__(self, item0, prev_list = None):
        if not prev_list:
            self.assignments = [item0]
        else:
            self.assignments = prev_list.assignments + [item0]
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment list'
        for item in self.assignments:
            item.debug_print(indentation + 2)

class ConstantString:
    def __init__(self, value):
        self.value = value
    def debug_print(self, indentation):
        print indentation*' ' + 'String: ' + self.value
    def write(self, file, full_string = True):
        file.write(self.value + " ")
        if full_string: file.write("00\n")

class ConstantNumeric(Expr):
    def __init__(self, value):
        self.value = value
    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value
    def write(self, file, size):
        print_varx(file, self.value, size)

class GRF:
    def __init__(self, alist):
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist.assignments:
            if not isinstance(assignment.value, ConstantString):
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
    def __init__(self, feature, id, expr, body):
        self.feature = feature
        self.id = id
        self.expr = expr
        self.body = body
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Switch, Feature =,',self.feature,', name =', self.id
        print (2+indentation)*' ' + 'Expression:'
        self.expr.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Body:'
        self.body.debug_print(indentation + 4)

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
