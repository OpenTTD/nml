import datetime, calendar
from nml import generic, nmlop

class Expression(object):
    """
    Superclass for all expression classes.

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """
    def __init__(self, pos):
        self.pos = pos

    def debug_print(self, indentation):
        """
        Print all data with explanation of what it is to standard output.
        
        @param indentation: Indent all printed lines with at least
            C{indentation} spaces.
        """
        raise NotImplementedError('debug_print must be implemented in expression-subclasses')

    def __str__(self):
        """
        Convert this expression to a string representing this expression in valid NML-code.
        
        @return: A string representation of this expression.
        """
        raise NotImplementedError('__str__ must be implemented in expression-subclasses')

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        """
        Reduce this expression to the simplest representation possible.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.
        @param unknown_id_fatal: Is encountering an unknown identifier somewhere
            in this expression a fatal error?

        @return: A deep copy of this expression simplified as much as possible.
        """
        raise NotImplementedError('reduce must be implemented in expression-subclasses')

    def reduce_constant(self, id_dicts = []):
        """
        Reduce this expression and make sure the result is a constant number.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.

        @return: A constant number that is the result of this expression.
        """
        expr = self.reduce(id_dicts)
        if not isinstance(expr, (ConstantNumeric, ConstantFloat)):
            raise generic.ConstError(self.pos)
        return expr

    def supported_by_action2(self, raise_error):
        """
        Check if this expression can be used inside a switch-block.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by advanced varaction2.
        """
        if raise_error: raise generic.ScriptError("This expression is not supported in a switch-block", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        """
        Check if this expression can be used inside a parameter-assignment.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by actionD.
        """
        if raise_error: raise generic.ScriptError("This expression can not be assigned to a parameter", self.pos)
        return False

    def is_boolean(self):
        """
        Check if this expression is limited to 0 or 1 as value.

        @return: True if the value of this expression is either 0 or 1.
        """
        return False

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

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        return True

    def is_boolean(self):
        return self.value == 0 or self.value == 1

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
        print indentation*' ' + 'Binary operator, op = ', self.op.token
        self.expr1.debug_print(indentation + 2)
        self.expr2.debug_print(indentation + 2)

    def __str__(self):
        return self.op.to_string(self.expr1, self.expr2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(expr1, ConstantNumeric) and isinstance(expr2, ConstantNumeric) and self.op.compiletime_func:
            return ConstantNumeric(self.op.compiletime_func(expr1.value, expr2.value), self.pos)
        if isinstance(expr1, StringLiteral) and isinstance(expr2, StringLiteral) and self.op == nmlop.ADD:
            return StringLiteral(expr1.value + expr2.value, expr1.pos)
        simple_expr1 = isinstance(expr1, (ConstantNumeric, Parameter, Variable))
        simple_expr2 = isinstance(expr2, (ConstantNumeric, Parameter, Variable))
        op = self.op
        if (simple_expr1 and not simple_expr2) or (isinstance(expr2, (Parameter, Variable)) and isinstance(expr1, ConstantNumeric)):
            if op in commutative_operators or self.op in (nmlop.CMP_LT, nmlop.CMP_GT):
                expr1, expr2 = expr2, expr1
                if op == nmlop.CMP_LT:
                    op = nmlop.CMP_GT
                elif op == nmlop.CMP_GT:
                    op = nmlop.CMP_LT
        if isinstance(expr1, Variable) and isinstance(expr2, ConstantNumeric):
            if op == nmlop.AND and isinstance(expr1.mask, ConstantNumeric):
                expr1.mask = ConstantNumeric(expr1.mask.value & expr2.value, self.pos)
                return expr1
            if op == nmlop.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = ConstantNumeric(expr1.add.value + expr2.value, self.pos)
                return expr1
            if op == nmlop.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(-expr2.value)
                else: expr1.add = ConstantNumeric(expr1.add.value - expr2.value, self.pos)
                return expr1
            if op == nmlop.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if op == nmlop.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
        return BinOp(op, expr1, expr2, self.pos)

    def supported_by_action2(self, raise_error):
        if not self.op.act2_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error: raise generic.ScriptError("Operator%s not supported in a switch-block" % token, self.pos)
            return False
        return self.expr1.supported_by_action2(raise_error) and self.expr2.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        if not self.op.actd_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error: raise generic.ScriptError("Operator%s not supported in parameter assignment" % token, self.pos)
            return False
        return self.expr1.supported_by_actionD(raise_error) and self.expr2.supported_by_actionD(raise_error)

    def is_boolean(self):
        return self.op.returns_boolean

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

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        return True

    def is_boolean(self):
        return self.expr1.is_boolean() and self.expr2.is_boolean()

class Boolean(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Force expression to boolean:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.is_boolean(): return expr
        return Boolean(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

class Not(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Logical not:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if isinstance(expr, ConstantNumeric): return ConstantNumeric(expr.value != 0)
        if isinstance(expr, Not): return expr.expr
        if isinstance(expr, BinOp):
            if expr.op == nmlop.CMP_EQ: return BinOp(nmlop.CMP_NEQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_NEQ: return BinOp(nmlop.CMP_EQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LE: return BinOp(nmlop.CMP_GT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GE: return BinOp(nmlop.CMP_LT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LT: return BinOp(nmlop.CMP_GE, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GT: return BinOp(nmlop.CMP_LE, expr.expr1, expr.expr2)
        return Not(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

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

    def supported_by_action2(self, raise_error):
        supported = isinstance(self.num, ConstantNumeric)
        if not supported and raise_error:
            raise generic.ScriptError("Parameters with non-constant numbers are not supported in a switch-block", self.pos)
        return supported

    def supported_by_actionD(self, raise_error):
        return True

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

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        if raise_error: raise generic.ScriptError("Variables are not supported in parameter assignments", self.pos)
        return False

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
                raise generic.ScriptError("Only built-in functions can accept parameters. '%s' is not a built-in function." % self.name.value, self.pos)
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
            id_d, func = (id_dict, lambda x, pos: StringLiteral(x, pos) if isinstance(x, basestring) else ConstantNumeric(x, pos)) if not isinstance(id_dict, tuple) else id_dict
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

#{ Builtin functions

def builtin_min(name, args, pos):
    """
    min(...) builtin function.

    @return Lowest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("min() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(nmlop.MIN, x, y, pos), args)

def builtin_max(name, args, pos):
    """
    max(...) builtin function.

    @return Heighest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("max() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(nmlop.MAX, x, y, pos), args)

def builtin_date(name, args, pos):
    """
    date(year, month, day) builtin function.

    @return Days since 1 jan 1 of the given date.
    """
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
        part1 = BinOp(nmlop.MUL, year, ConstantNumeric(365))
        part2 = BinOp(nmlop.DIV, year, ConstantNumeric(4))
        part3 = BinOp(nmlop.DIV, year, ConstantNumeric(100))
        part4 = BinOp(nmlop.DIV, year, ConstantNumeric(400))
        res = BinOp(nmlop.ADD, part1, part2)
        res = BinOp(nmlop.SUB, res, part3)
        res = BinOp(nmlop.ADD, res, part4)
        return res
    date = datetime.date(year.value, month, day)
    return ConstantNumeric(year.value * 365 + calendar.leapdays(0, year.value) + date.timetuple().tm_yday - 1, pos)

def builtin_day_of_year(name, args, pos):
    """
    day_of_year(month, day) builtin function.

    @return Day of the year, assuming February has 28 days.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have a month and a day parameter", pos)

    month = args[0].reduce()
    if not isinstance(month, ConstantNumeric):
        raise generic.ScriptError('Month should be a compile-time constant.', month.pos)
    if month.value < 1 or month.value > 12:
        raise generic.ScriptError('Month should be a value between 1 and 12.', month.pos)

    day = args[0].reduce()
    if not isinstance(day, ConstantNumeric):
        raise generic.ScriptError('Day should be a compile-time constant.', day.pos)

    # Mapping of month to number of days in that month.
    number_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if day.value < 1 or day.value > number_days[month.value]:
        raise generic.ScriptError('Day should be value between 1 and %d.' % number_days[month.value], day.pos)

    return ConstantNumeric(datetime.date(1, month.value, day.value).toordinal(), pos)


def builtin_store(name, args, pos):
    """
    STORE_TEMP(value, pos) builtin function.
    STORE_PERM(value, pos) builtin function.
    Store C{value} in temporary/permanent storage in location C{pos}.

    @return C{value}
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    op = nmlop.STO_TMP if name == 'STORE_TEMP' else nmlop.STO_PERM
    return BinOp(op, args[0], args[1], pos)

def builtin_load(name, args, pos):
    """
    LOAD_TEMP(pos) builtin function.
    LOAD_PERM(pos) builtin function.
    Load a value from location C{pos} from temporary/permanent storage.

    @return The value loaded from the storage.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have one parameter", pos)
    var_num = 0x7D if name == "LOAD_TEMP" else 0x7C
    return Variable(ConstantNumeric(var_num), param=args[0], pos=pos)

def builtin_hasbit(name, args, pos):
    """
    hasbit(value, bit_num) builtin function.

    @return C{1} if and only if C{value} has bit C{bit_num} set, C{0} otherwise.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(nmlop.HASBIT, args[0], args[1], pos)

def builtin_version_openttd(name, args, pos):
    """
    version_openttd(major, minor, revision[, build]) builtin function.

    @return The version information encoded in a double-word.
    """
    if len(args) > 4 or len(args) < 3:
        raise generic.ScriptError(name + "() must have 3 or 4 parameters", pos)
    major = args[0].reduce_constant().value
    minor = args[1].reduce_constant().value
    revision = args[2].reduce_constant().value
    build = args[3].reduce_constant().value if len(args) == 4 else 0x80000
    return ConstantNumeric((major << 28) | (minor << 24) | (revision << 20) | build)

#}

function_table = {
    'min' : builtin_min,
    'max' : builtin_max,
    'date' : builtin_date,
    'day_of_year' : builtin_day_of_year,
    'bitmask' : lambda name, args, pos: BitMask(args, pos),
    'STORE_TEMP' : builtin_store,
    'STORE_PERM' : builtin_store,
    'LOAD_TEMP' : builtin_load,
    'LOAD_PERM' : builtin_load,
    'hasbit' : builtin_hasbit,
    'version_openttd' : builtin_version_openttd,
}

commutative_operators = set([
    nmlop.ADD,
    nmlop.MUL,
    nmlop.AND,
    nmlop.OR,
    nmlop.XOR,
    nmlop.CMP_EQ,
    nmlop.CMP_NEQ,
    nmlop.MIN,
    nmlop.MAX,
])
