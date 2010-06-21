import operator
import datetime, calendar
from nml import generic

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
    HASBIT  = 19


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

class Expression(object):
    def __init__(self, pos):
        self.pos = pos

    def reduce_constant(self, id_dicts = []):
        expr = self.reduce(id_dicts)
        if not isinstance(expr, (ConstantNumeric, ConstantFloat)):
            raise generic.ConstError(self.pos)
        return expr

class ConstantNumeric(Expression):
    def __init__(self, value, pos = None):
        Expression.__init__(self, pos)
        self.value = generic.truncate_int32(value)

    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value

    def write(self, file, size):
        file.print_varx(self.value, size)

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class ConstantFloat(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Float:', self.value

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class BitMask(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        ret = 0
        for orig_expr in self.values:
            val = orig_expr.reduce_constant(id_dicts) # unknown ids are always fatal as they're not compile time constant
            if val.value >= 32: raise generic.ScriptError("Parameters of 'bitmask' cannot be greater then 31", orig_expr.pos)
            ret |= 1 << val.value
        return ConstantNumeric(ret, self.pos)

class BinOp(Expression):
    def __init__(self, op, expr1, expr2, pos = None):
        Expression.__init__(self, pos)
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
            return ConstantNumeric(compile_time_operator[self.op](expr1.value, expr2.value), self.pos)
        if isinstance(expr1, StringLiteral) and isinstance(expr2, StringLiteral) and self.op == Operator.ADD:
            return StringLiteral(expr1.value + expr2.value, expr1.pos)
        simple_expr1 = isinstance(expr1, (ConstantNumeric, Parameter, Variable))
        simple_expr2 = isinstance(expr2, (ConstantNumeric, Parameter, Variable))
        op = self.op
        if (simple_expr1 and not simple_expr2) or (isinstance(expr2, Variable) and isinstance(expr1, ConstantNumeric)):
            if op in commutative_operators or self.op in (Operator.CMP_LT, Operator.CMP_GT):
                expr1, expr2 = expr2, expr1
                if op == Operator.CMP_LT:
                    op = Operator.CMP_GT
                elif op == Operator.CMP_GT:
                    op = Operator.CMP_LT
        if isinstance(expr1, Variable) and isinstance(expr2, ConstantNumeric):
            if op == Operator.AND and isinstance(expr1.mask, ConstantNumeric):
                expr1.mask = ConstantNumeric(expr1.mask.value & expr2.value, self.pos)
                return expr1
            if op == Operator.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = ConstantNumeric(expr1.add.value + expr2.value, self.pos)
                return expr1
            if op == Operator.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(-expr2.value)
                else: expr1.add = ConstantNumeric(expr1.add.value - expr2.value, self.pos)
                return expr1
            if op == Operator.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if op == Operator.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
        return BinOp(op, expr1, expr2, self.pos)

class TernaryOp(Expression):
    def __init__(self, guard, expr1, expr2, pos):
        Expression.__init__(self, pos)
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
        guard = self.guard.reduce(id_dicts)
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(guard, ConstantNumeric):
            if guard.value != 0:
                return expr1
            else:
                return expr2
        return TernaryOp(guard, expr1, expr2, self.pos)

class Parameter(Expression):
    def __init__(self, num, pos = None):
        Expression.__init__(self, pos)
        self.num = num

    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return 'param[%s]' % str(self.num)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        num = self.num.reduce(id_dicts)
        return Parameter(num, self.pos)

class Variable(Expression):
    def __init__(self, num, shift = None, mask = None, param = None, pos = None):
        Expression.__init__(self, pos)
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
        param = self.param.reduce(id_dicts) if self.param is not None else None
        var = Variable(num, shift, mask, param, self.pos)
        var.add = self.add
        var.div = self.div
        var.mod = self.mod
        return var

class FunctionCall(Expression):
    def __init__(self, name, params, pos):
        Expression.__init__(self, pos)
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
            val = func(self.name.value, param_list, self.pos)
            return val.reduce(id_dicts)
        else:
            if len(param_list) != 0:
                raise generic.ScriptError("Only built-in functions can accept parameters. '%s' is not a built-in function." % self.name.value, self.pos);
            return Variable(ConstantNumeric(0x7E), param=self.name.value, pos = self.pos)

class String(Expression):
    def __init__(self, name, params, pos):
        Expression.__init__(self, pos)
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

class Identifier(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'ID: ' + self.value

    def __str__(self):
        return self.value

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x, pos: ConstantNumeric(x, pos)) if not isinstance(id_dict, tuple) else id_dict
            if self.value in id_d:
                return func(id_d[self.value], self.pos)
        if unknown_id_fatal: raise generic.ScriptError("Unrecognized identifier '" + self.value + "' encountered", self.pos)
        return self

class StringLiteral(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
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

class Array(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Array of values:'
        for v in self.values:
            v.debug_print(indentation + 2)

    def __str__(self):
        return '[' + ', '.join([str(expr) for expr in self.values]) + ']'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return Array([val.reduce(id_dicts, unknown_id_fatal) for val in self.values], self.pos)

#
# compile-time expression evaluation
#

def builtin_min(name, args, pos):
    if len(args) < 2:
        raise generic.ScriptError("min() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(Operator.MIN, x, y, pos), args)

def builtin_max(name, args, pos):
    if len(args) < 2:
        raise generic.ScriptError("max() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(Operator.MAX, x, y, pos), args)

def builtin_date(name, args, pos):
    if len(args) != 3:
        raise generic.ScriptError("date() requires exactly 3 arguments", pos)
    year = args[0].reduce()
    try:
        month = args[1].reduce_constant().value
        day = args[2].reduce_constant().value
    except generic.ConstError:
        raise generic.ScriptError("Month and day parameters of date() should be compile-time constants", pos)
    if not isinstance(year, ConstantNumeric):
        if month != 1 or day != 1:
            raise generic.ScriptError("when the year parameter of date() is not a compile time constant month and day should be 1", pos)
        #num_days = year*365 + year/4 - year/100 + year/400
        part1 = BinOp(Operator.MUL, year, ConstantNumeric(365))
        part2 = BinOp(Operator.DIV, year, ConstantNumeric(4))
        part3 = BinOp(Operator.DIV, year, ConstantNumeric(100))
        part4 = BinOp(Operator.DIV, year, ConstantNumeric(400))
        res = BinOp(Operator.ADD, part1, part2)
        res = BinOp(Operator.SUB, res, part3)
        res = BinOp(Operator.ADD, res, part4)
        return res
    date = datetime.date(year.value, month, day)
    return ConstantNumeric(year.value * 365 + calendar.leapdays(0, year.value) + date.timetuple().tm_yday - 1, pos)

def builtin_store(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    op = Operator.STO_TMP if name == 'STORE_TEMP' else Operator.STO_PERM
    return BinOp(op, args[0], args[1], pos)

def builtin_load(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have one parameter", pos)
    var_num = 0x7D if name == "LOAD_TEMP" else 0x7C
    return Variable(ConstantNumeric(var_num), param=args[0], pos=pos)

def builtin_hasbit(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(Operator.HASBIT, args[0], args[1], pos)

function_table = {
    'min' : builtin_min,
    'max' : builtin_max,
    'date' : builtin_date,
    'bitmask' : lambda name, args, pos: BitMask(args, pos),
    'STORE_TEMP' : builtin_store,
    'STORE_PERM' : builtin_store,
    'LOAD_TEMP' : builtin_load,
    'LOAD_PERM' : builtin_load,
    'hasbit' : builtin_hasbit,
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
    Operator.HASBIT:  lambda a, b: (a & (1 << b)) != 0,
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
