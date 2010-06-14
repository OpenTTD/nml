import operator
import datetime, calendar
from nml import generic

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
        self.value = generic.truncate_int32(value)

    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value

    def write(self, file, size):
        file.print_varx(self.value, size)

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class ConstantFloat(object):
    def __init__(self, value):
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Float:', self.value

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class BitMask(object):
    def __init__(self, values):
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        ret = 0
        for orig_expr in self.values:
            val = orig_expr.reduce(id_dicts) # unknown ids are always fatal as they're not compile time constant
            if not isinstance(val, ConstantNumeric): raise generic.ScriptError("Parameters of 'bitmask' should be a constant")
            if val.value >= 32: raise generic.ScriptError("Parameters of 'bitmask' cannot be greater then 31")
            ret |= 1 << val.value
        return ConstantNumeric(ret)

class BinOp(object):
    def __init__(self, op, expr1, expr2):
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op
        self.expr1.debug_print(indentation + 2)
        self.expr2.debug_print(indentation + 2)

    def __str__(self):
        return get_operator_string(self.op, str(self.expr1), str(self.expr2))

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(expr1, ConstantNumeric) and isinstance(expr2, ConstantNumeric) and self.op in compile_time_operator:
            return ConstantNumeric(compile_time_operator[self.op](expr1.value, expr2.value))
        simple_expr1 = isinstance(expr1, (ConstantNumeric, Parameter, Variable))
        simple_expr2 = isinstance(expr2, (ConstantNumeric, Parameter, Variable))
        if self.op in commutative_operators and ((simple_expr1 and not simple_expr2) or (isinstance(expr2, Variable) and isinstance(expr1, ConstantNumeric))):
            expr1, expr2 = expr2, expr1
        if isinstance(expr1, Variable) and isinstance(expr2, ConstantNumeric):
            if self.op == Operator.AND and isinstance(expr1.mask, ConstantNumeric):
                expr1.mask = ConstantNumeric(expr1.mask.value & expr2.value)
                return expr1
            if self.op == Operator.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = ConstantNumeric(expr1.add.value + expr2.value)
                return expr1
            if self.op == Operator.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(-expr2.value)
                else: expr1.add = ConstantNumeric(expr1.add.value - expr2.value)
                return expr1
            if self.op == Operator.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if self.op == Operator.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
        return BinOp(self.op, expr1, expr2)

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

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        guard = self.guard.reduce(self.guard)
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(guard, ConstantNumeric):
            if guard.value != 0:
                return expr1
            else:
                return expr2
        return TernaryOp(guard, expr1, expr2)

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

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        num = self.num.reduce(id_dicts)
        return Parameter(num)

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

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        num = self.num.reduce(id_dicts)
        shift = self.shift.reduce(id_dicts)
        mask = self.mask.reduce(id_dicts)
        param = self.param.reduce(id_dicts)
        var = Variable(num, shift, mask, param)
        var.add = self.add
        var.div = self.div
        var.mod = self.mod
        return var

class FunctionCall(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def debug_print(self, indentation):
        print indentation*' ' + 'Call function: ' + self.name.value
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = ''
        for param in self.params:
            if ret == '': ret = str(param)
            else: ret = '%s, %s' % (ret, str(param))
        ret = '%s(%s)' % (self.name, ret)
        return ret

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        param_list = []
        for param in self.params:
            param_list.append(param.reduce(id_dicts))
        if self.name.value in function_table:
            func = function_table[self.name.value]
            val = func(self.name.value, param_list)
            return val.reduce(id_dicts)
        else:
            if len(param_list) != 0:
                raise generic.ScriptError("Only built-in functions can accept parameters. '%s' is not a built-in function." % self.name.value);
            return Variable(ConstantNumeric(0x7E), param=self.name.value)

class String(object):
    def __init__(self, name, params = []):
        self.name = name
        self.params = params

    def debug_print(self, indentation):
        print indentation*' ' + 'String:'
        self.name.debug_print(indentation + 2)
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = 'string(' + self.name.value
        for p in self.params:
            ret += ', ' + str(p)
        ret += ')'
        return ret

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class Identifier(object):
    def __init__(self, value):
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'ID: ' + self.value

    def __str__(self):
        return self.value

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x: ConstantNumeric(x)) if not isinstance(id_dict, tuple) else id_dict
            if self.value in id_d:
                return func(id_d[self.value])
        if unknown_id_fatal: raise generic.ScriptError("Unrecognized identifier '" + self.value + "' encountered")

class StringLiteral(object):
    def __init__(self, value):
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'String literal: "%s"' % self.value

    def __str__(self):
        return '"%s"' % self.value

    def write(self, file, size):
        assert(len(self.value) == size)
        file.print_string(self.value, final_zero = False, force_ascii = True)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class Array(object):
    def __init__(self, values):
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Array of values:'
        for v in self.values:
            v.debug_print(indentation + 2)

    def __str__(self):
        return '[' + ', '.join([str(expr) for expr in self.values]) + ']'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return Array([val.reduce(id_dicts, unknown_id_fatal) for val in self.values])

#
# compile-time expression evaluation
#

def builtin_min(name, args):
    if len(args) < 2:
        raise generic.ScriptError("min() requires at least 2 arguments")
    return reduce(lambda x, y: BinOp(Operator.MIN, x, y), args)

def builtin_max(name, args):
    if len(args) < 2:
        raise generic.ScriptError("max() requires at least 2 arguments")
    return reduce(lambda x, y: BinOp(Operator.MAX, x, y), args)

def builtin_date(name, args):
    if len(args) != 3:
        raise generic.ScriptError("date() requires exactly 3 arguments")
    try:
        year = reduce_constant(args[0]).value
        month = reduce_constant(args[1]).value
        day = reduce_constant(args[2]).value
    except generic.ConstError:
        raise generic.ScriptError("Parameters of date() should be compile-time constants")
    date = datetime.date(year, month, day)
    return ConstantNumeric(year * 365 + calendar.leapdays(0, year) + date.timetuple().tm_yday - 1)

def builtin_store(name, args):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters")
    op = Operator.STO_TMP if name == 'STORE_TEMP' else Operator.STO_PERM
    return BinOp(op, args[0], args[1])

def builtin_load(name, args):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have one parameter")
    var_num = 0x7D if name == "LOAD_TEMP" else 0x7C
    return Variable(ConstantNumeric(var_num), param=args[0])

function_table = {
    'min' : builtin_min,
    'max' : builtin_max,
    'date' : builtin_date,
    'bitmask' : lambda name, args: BitMask(args),
    'STORE_TEMP' : builtin_store,
    'STORE_PERM' : builtin_store,
    'LOAD_TEMP' : builtin_load,
    'LOAD_PERM' : builtin_load,
}


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

commutative_operators = set([
    Operator.ADD,
    Operator.MUL,
    Operator.AND,
    Operator.OR,
    Operator.XOR,
    Operator.CMP_EQ,
    Operator.CMP_NEQ,
    Operator.MIN,
    Operator.MAX,
])

def reduce_constant(expr, id_dicts = []):
    expr = expr.reduce(id_dicts)
    if not isinstance(expr, (ConstantNumeric, ConstantFloat)):
        raise generic.ConstError()
    return expr
