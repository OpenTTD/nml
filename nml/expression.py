import operator
from generic import *

cargo_numbers = {}
item_names = {}

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
    STO_TMP = 15
    STO_PERM = 16

class ConstantNumeric:
    def __init__(self, value):
        self.value = truncate_int32(value)
    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value
    def write(self, file, size):
        print_varx(file, self.value, size)

class BitMask:
    def __init__(self, values):
        self.values = values
    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

class BinOp:
    def __init__(self, op, expr1, expr2):
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op
        if isinstance(self.expr1, basestring):
            print (indentation+2)*' ' + 'ID:', self.expr1
        else:
            self.expr1.debug_print(indentation + 2)
        if isinstance(self.expr2, basestring):
            print (indentation+2)*' ' + 'ID:', self.expr2
        else:
            self.expr2.debug_print(indentation + 2)

class TernaryOp:
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

class Parameter:
    def __init__(self, num):
        self.num = num
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)

class Variable:
    def __init__(self, num, shift = None, mask = None, param = None):
        self.num = num
        self.shift = shift if shift != None else ConstantNumeric(0)
        self.mask = mask if mask != None else ConstantNumeric(0xFFFFFFFF)
        self.param = param
        self.add = None
        self.div = None
        self.mod = None
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Action2 variable'
        self.num.debug_print(indentation + 2)
        if self.param != None:
            print (indentation+2)*' ' + 'Parameter:'
            if isinstance(self.param, basestring):
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

commutative_operators = [
    Operator.ADD,
    Operator.MUL,
    Operator.AND,
    Operator.OR,
    Operator.XOR,
    Operator.CMP_EQ,
    Operator.CMP_NEQ,
    Operator.MIN,
    Operator.MAX,
]

# note: id_dicts is a *list* of dictionaries or (dictionary, function)-tuples
def reduce_expr(expr, id_dicts = []):
    global compile_time_operator
    if isinstance(expr, BinOp):
        expr.expr1 = reduce_expr(expr.expr1, id_dicts)
        expr.expr2 = reduce_expr(expr.expr2, id_dicts)
        if isinstance(expr.expr1, ConstantNumeric) and isinstance(expr.expr2, ConstantNumeric):
            return ConstantNumeric(compile_time_operator[expr.op](expr.expr1.value, expr.expr2.value))
        simple_expr1 = isinstance(expr.expr1, ConstantNumeric) or isinstance(expr.expr1, Parameter) or isinstance(expr.expr1, Variable)
        simple_expr2 = isinstance(expr.expr2, ConstantNumeric) or isinstance(expr.expr2, Parameter) or isinstance(expr.expr2, Variable)
        if expr.op in commutative_operators and ((simple_expr1 and not simple_expr2) or (isinstance(expr.expr2, Variable) and isinstance(expr.expr1, ConstantNumeric))):
            expr.expr1, expr.expr2 = expr.expr2, expr.expr1
        if isinstance(expr.expr1, Variable) and isinstance(expr.expr2, ConstantNumeric):
            if expr.op == Operator.AND and isinstance(expr.expr1.mask, ConstantNumeric):
                expr.expr1.mask = ConstantNumeric(expr.expr1.mask.value & expr.expr2.value)
                return expr.expr1
            if expr.op == Operator.ADD and expr.expr1.div == None and expr.expr1.mod == None:
                if expr.expr1.add == None: expr.expr1.add = expr.expr2
                else: expr.expr1.add = ConstantNumeric(expr.expr1.add + expr.expr2.value)
                return expr.expr1
            if expr.op == Operator.SUB and expr.expr1.div == None and expr.expr1.mod == None:
                if expr.expr1.add == None: expr.expr1.add = ConstantNumeric(-expr.expr2.value)
                else: expr.expr1.add = ConstantNumeric(expr.expr1.add - expr.expr2.value)
                return expr.expr1
            if expr.op == Operator.DIV and expr.expr1.div == None and expr.expr1.mod == None:
                if expr.expr1.add == None: expr.expr1.add = ConstantNumeric(0)
                expr.expr1.div = expr.expr2
                return expr.expr1
            if expr.op == Operator.MOD and expr.expr1.div == None and expr.expr1.mod == None:
                if expr.expr1.add == None: expr.expr1.add = ConstantNumeric(0)
                expr.expr1.mod = expr.expr2
                return expr.expr1
    elif isinstance(expr, Parameter):
        expr.num = reduce_expr(expr.num, id_dicts)
    elif isinstance(expr, Variable):
        expr.num = reduce_expr(expr.num, id_dicts)
        expr.shift = reduce_expr(expr.shift, id_dicts)
        expr.mask = reduce_expr(expr.mask, id_dicts)
        expr.param = reduce_expr(expr.param, id_dicts)
    elif isinstance(expr, basestring):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x: ConstantNumeric(x)) if not isinstance(id_dict, tuple) else id_dict
            if expr in id_d:
                return func(id_d[expr])
        raise ScriptError("Unrecognized identifier '" + expr + "' encountered")
    elif isinstance(expr, BitMask):
        ret = 0
        for orig_expr in expr.values:
            val = reduce_expr(orig_expr, id_dicts)
            if not isinstance(val, ConstantNumeric): raise ScriptError("Parameters of 'bit' should be a constant")
            if val.value >= 32: raise ScriptError("Parameters of 'bit' cannot be greater then 31")
            ret |= 1 << val.value
        return ConstantNumeric(ret)
    return expr

def reduce_constant(expr, id_dicts = []):
    expr = reduce_expr(expr, id_dicts)
    if not isinstance(expr, ConstantNumeric):
        raise ConstError()
    return expr
