import operator
from generic import *

cargo_numbers = {}
item_names = {}

class Operator(object):
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
    SHIFT_LEFT = 17
    SHIFT_RIGHT = 18


def get_operator_string(op, param1, param2):
    operator_to_string = {}
    operator_to_string[Operator.ADD] = '(%s + %s)'
    operator_to_string[Operator.SUB] = '(%s - %s)'
    operator_to_string[Operator.DIV] = '(%s / %s)'
    operator_to_string[Operator.MOD] = '(%s %% %s)'
    operator_to_string[Operator.MUL] = '(%s * %s)'
    operator_to_string[Operator.AND] = '(%s & %s)'
    operator_to_string[Operator.OR] = '(%s | %s)'
    operator_to_string[Operator.XOR] = '(%s ^ %s)'
    #operator_to_string[Operator.VAL2] = 
    operator_to_string[Operator.CMP_EQ] = '(%s == %s)'
    operator_to_string[Operator.CMP_NEQ] = '(%s != %s)'
    operator_to_string[Operator.CMP_LT] = '(%s < %s)'
    operator_to_string[Operator.CMP_GT] = '(%s > %s)'
    operator_to_string[Operator.MIN] = 'min(%s, %s)'
    operator_to_string[Operator.MAX] = 'max(%s, %s)'
    operator_to_string[Operator.STO_TMP] = 'STORE_TEMP(%s, %s)'
    operator_to_string[Operator.STO_PERM] = 'STORE_PERM(%s, %s)'
    operator_to_string[Operator.SHIFT_LEFT] = '(%s << %s)'
    operator_to_string[Operator.SHIFT_RIGHT] = '(%s >> %s)'
    return operator_to_string[op] % (param1, param2)

class ConstantNumeric(object):
    def __init__(self, value):
        self.value = truncate_int32(value)
    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value
    def write(self, file, size):
        file.print_varx(self.value, size)
    def __str__(self):
        return str(self.value)

class ConstantFloat(object):
    def __init__(self, value):
        self.value = value
    def debug_print(self, indentation):
        print indentation*' ' + 'Float:', self.value
    def __str__(self):
        return str(self.value)

class BitMask(object):
    def __init__(self, values):
        self.values = values
    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

class BinOp(object):
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
    
    def __str__(self):
        return get_operator_string(self.op, str(self.expr1), str(self.expr2))

class TernaryOp(object):
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

class Assignment(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)

class Parameter(object):
    def __init__(self, num):
        self.num = num
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)
    def __str__(self):
        return 'param[%s]' % str(self.num)

class Variable(object):
    def __init__(self, num, shift = None, mask = None, param = None):
        self.num = num
        self.shift = shift if shift is not None else ConstantNumeric(0)
        self.mask = mask if mask is not None else ConstantNumeric(0xFFFFFFFF)
        self.param = param
        self.add = None
        self.div = None
        self.mod = None

    def debug_print(self, indentation):
        print indentation*' ' + 'Action2 variable'
        self.num.debug_print(indentation + 2)
        if self.param is not None:
            print (indentation+2)*' ' + 'Parameter:'
            if isinstance(self.param, basestring):
                print (indentation+4)*' ' + 'Procedure call:', self.param
            else:
                self.param.debug_print(indentation + 4)

    def __str__(self):
        ret = 'var[%s, %s, %s' % (str(self.num), str(self.shift), str(self.mask))
        if self.param is not None:
            ret += ', %s' & str(self.param)
        ret += ']'
        if self.add is not None:
            ret = '(%s + %s)' % (ret, self.add)
        if self.div is not None:
            ret = '(%s / %s)' % (ret, self.div)
        if self.mod is not None:
            ret = '(%s %% %s)' % (ret, self.mod)
        return ret

class String(object):
    def __init__(self, name, params = []):
        self.name = name
        self.params = params
    def debug_print(self, indentation):
        print indentation*' ' + 'String: ' + self.name
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)
    def __str__(self):
        ret = 'string(' + self.name
        for p in self.params:
            ret += ', ' . str(p)
        ret += ')'
        return ret


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
    Operator.MAX:     lambda a, b: max(a, b),
    Operator.SHIFT_LEFT: operator.lshift,
    Operator.SHIFT_RIGHT: operator.rshift,
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
def reduce_expr(expr, id_dicts = [], unkown_id_fatal = True):
    global compile_time_operator
    if isinstance(expr, BinOp):
        expr1 = reduce_expr(expr.expr1, id_dicts)
        expr2 = reduce_expr(expr.expr2, id_dicts)
        if isinstance(expr1, ConstantNumeric) and isinstance(expr2, ConstantNumeric):
            return ConstantNumeric(compile_time_operator[expr.op](expr1.value, expr2.value))
        simple_expr1 = isinstance(expr1, ConstantNumeric) or isinstance(expr1, Parameter) or isinstance(expr1, Variable)
        simple_expr2 = isinstance(expr2, ConstantNumeric) or isinstance(expr2, Parameter) or isinstance(expr2, Variable)
        if expr.op in commutative_operators and ((simple_expr1 and not simple_expr2) or (isinstance(expr2, Variable) and isinstance(expr1, ConstantNumeric))):
            expr1, expr2 = expr2, expr1
        if isinstance(expr1, Variable) and isinstance(expr2, ConstantNumeric):
            if expr.op == Operator.AND and isinstance(expr1.mask, ConstantNumeric):
                expr1.mask = ConstantNumeric(expr1.mask.value & expr2.value)
                return expr1
            if expr.op == Operator.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = ConstantNumeric(expr1.add.value + expr2.value)
                return expr1
            if expr.op == Operator.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(-expr2.value)
                else: expr1.add = ConstantNumeric(expr1.add.value - expr2.value)
                return expr1
            if expr.op == Operator.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if expr.op == Operator.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
        return BinOp(expr.op, expr1, expr2)
    elif isinstance(expr, Parameter):
        if not isinstance(expr.num, ConstantNumeric):
            return Parameter(reduce_expr(expr.num, id_dicts))
    elif isinstance(expr, Variable):
        num = reduce_expr(expr.num, id_dicts)
        shift = reduce_expr(expr.shift, id_dicts)
        mask = reduce_expr(expr.mask, id_dicts)
        param = reduce_expr(expr.param, id_dicts)
        var = Variable(num, shift, mask, param)
        var.add = expr.add
        var.div = expr.div
        var.mod = expr.mod
        return var
    elif isinstance(expr, basestring):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x: ConstantNumeric(x)) if not isinstance(id_dict, tuple) else id_dict
            if expr in id_d:
                return func(id_d[expr])
        if unkown_id_fatal: raise ScriptError("Unrecognized identifier '" + expr + "' encountered")
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
    if not (isinstance(expr, ConstantNumeric) or isinstance(expr, ConstantFloat)):
        raise ConstError()
    return expr
