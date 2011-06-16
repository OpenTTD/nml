import datetime, calendar, math
from nml import generic, nmlop
from .base_expression import Type, Expression, ConstantNumeric, ConstantFloat
from .binop import BinOp
from .bitmask import BitMask
from .parameter import parse_string_to_dword
from .storage_op import StorageOp
from .string_literal import StringLiteral
from .ternaryop import TernaryOp
from .variable import Variable

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
            param_list.append(param.reduce(id_dicts, unknown_id_fatal))
        if self.name.value in function_table:
            func = function_table[self.name.value]
            val = func(self.name.value, param_list, self.pos)
            return val.reduce(id_dicts)
        else:
            #try user-defined functions
            func_ptr = self.name.reduce(id_dicts, False, True)
            if func_ptr != self.name: # we found something!
                if func_ptr.type() != Type.FUNCTION_PTR:
                    raise generic.ScriptError("'%s' is defined, but it is not a function." % self.name.value, self.pos)
                return func_ptr.call(param_list)
            if unknown_id_fatal:
                raise generic.ScriptError("'%s' is not defined as a function." % self.name.value, self.pos)
            return FunctionCall(self.name, param_list, self.pos)


class SpecialCheck(Expression):
    """
    Action7/9 special check (e.g. to see whether a cargo is defined)

    @ivar op: Action7/9 operator to use
    @type op: (C{int}, C{basestring})-tuple

    @ivar varnum: Variable number to read
    @type varnum: C{int}

    @ivar results: Result of the check when skipping (0) or not skipping (1)
    @type results: (C{int}, C{int})-tuple

    @ivar value: Value to test
    @type value: C{int}

    @ivar mask: Mask to to test only certain bits of the value
    @type mask: C{int}

    @ivar pos: Position information
    @type pos: L{Position}
    """
    def __init__(self, op, varnum, results, value, to_string, mask = None, pos = None):
        Expression.__init__(self, pos)
        self.op = op
        self.varnum = varnum
        self.results = results
        self.value = value
        self.to_string = to_string
        self.mask = mask

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def __str__(self):
        return self.to_string

    def supported_by_actionD(self, raise_error):
        return True

class GRMOp(Expression):
    def __init__(self, op, feature, count, to_string, pos = None):
        Expression.__init__(self, pos)
        self.op = op
        self.feature = feature
        self.count = count
        self.to_string = to_string

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def __str__(self):
        return self.to_string(self)

    def supported_by_actionD(self, raise_error):
        return True


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
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_in_year = 0
    for i in range(month - 1):
        day_in_year += days_in_month[i]
    day_in_year += day
    if month >= 3 and (year.value % 4 == 0) and ((not year.value % 100 == 0) or (year.value % 400 == 0)):
        day_in_year += 1
    return ConstantNumeric(year.value * 365 + calendar.leapdays(0, year.value) + day_in_year - 1, pos)

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

    day = args[1].reduce()
    if not isinstance(day, ConstantNumeric):
        raise generic.ScriptError('Day should be a compile-time constant.', day.pos)

    # Mapping of month to number of days in that month.
    number_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if day.value < 1 or day.value > number_days[month.value]:
        raise generic.ScriptError('Day should be value between 1 and %d.' % number_days[month.value], day.pos)

    return ConstantNumeric(datetime.date(1, month.value, day.value).toordinal(), pos)

def builtin_storage(name, args, pos):
    """
    Accesses to temporary / persistent storage
    """
    return StorageOp(name, args, pos)

def builtin_ucmp(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(nmlop.VACT2_UCMP, args[0], args[1], pos)

def builtin_cmp(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(nmlop.VACT2_CMP, args[0], args[1], pos)

def builtin_rotate(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(nmlop.ROT_RIGHT, args[0], args[1], pos)

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

def builtin_cargotype_available(name, args, pos):
    """
    cargotype_available(cargo_label) builtin function.

    @return 1 if the cargo label is available, 0 otherwise.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have exactly 1 parameter", pos)
    label = args[0].reduce()
    return SpecialCheck((0x0B, r'\7c'), 0, (0, 1), parse_string_to_dword(label), "%s(%s)" % (name, str(label)), pos = args[0].pos)

def builtin_railtype_available(name, args, pos):
    """
    railtype_available(cargo_label) builtin function.

    @return 1 if the railtype label is available, 0 otherwise.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have exactly 1 parameter", pos)
    label = args[0].reduce()
    return SpecialCheck((0x0D, None), 0, (0, 1), parse_string_to_dword(label), "%s(%s)" % (name, str(label)), pos = args[0].pos)

def builtin_grf_status(name, args, pos):
    """
    grf_(current_status|future_status|order_behind)(grfid[, mask]) builtin function.

    @return 1 if the grf is, or will be, active, 0 otherwise.
    """
    if len(args) not in (1, 2):
        raise generic.ScriptError(name + "() must have 1 or 2 parameters", pos)
    labels = [label.reduce() for label in args]
    mask = parse_string_to_dword(labels[1]) if len(labels) > 1 else None
    if name == 'grf_current_status':
        op = (0x06, r'\7G')
        results = (1, 0)
    elif name == 'grf_future_status':
        op = (0x0A, r'\7gg')
        results = (0, 1)
    elif name == 'grf_order_behind':
        op = (0x08, r'\7gG')
        results = (0, 1)
    else:
        assert False, "Unknown grf status function"
    if mask is None:
        string = "%s(%s)" % (name, str(label))
    else:
        string = "%s(%s, %s)" % (name, str(label), str(mask))
    return SpecialCheck(op, 0x88, results, parse_string_to_dword(labels[0]), string, mask, args[0].pos)

def builtin_visual_effect_and_powered(name, args, pos):
    """
    visual_effect_and_powered(effect, offset, powered) builtin function. Use this to set
    the train property visual_effect_and_powered and for the callback VEH_CB_VISUAL_EFFECT_AND_POWERED
    """
    if len(args) != 3:
        raise generic.ScriptError(name + "() must have 3 parameters", pos)
    from nml import global_constants
    effect = args[0].reduce_constant(global_constants.const_list).value
    offset = BinOp(nmlop.ADD, args[1], ConstantNumeric(8), args[1].pos).reduce_constant().value
    generic.check_range(offset, 0, 0x0F, "offset in function visual_effect_and_powered", pos)
    powered = args[2].reduce_constant(global_constants.const_list).value
    if powered != 0 and powered != 0x80:
        raise generic.ScriptError("3rd argument to visual_effect_and_powered (powered) must be either ENABLE_WAGON_POWER or DISABLE_WAGON_POWER", pos)
    return ConstantNumeric(effect | offset | powered)

def builtin_str2number(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    return ConstantNumeric(parse_string_to_dword(args[0]))

def builtin_cargotype(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    from nml import global_constants
    if not isinstance(args[0], StringLiteral) or args[0].value not in global_constants.cargo_numbers:
        raise generic.ScriptError("Parameter for " + name + "() must be a string literal that is also in your cargo table", pos)
    return ConstantNumeric(global_constants.cargo_numbers[args[0].value])

def builtin_railtype(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    from nml import global_constants
    if not isinstance(args[0], StringLiteral) or args[0].value not in global_constants.railtype_table:
        raise generic.ScriptError("Parameter for " + name + "() must be a string literal that is also in your railtype table", pos)
    return ConstantNumeric(global_constants.railtype_table[args[0].value])

def builtin_reserve_sprites(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    count = args[0].reduce_constant()
    func = lambda x: '%s(%d)' % (name, count.value)
    return GRMOp(nmlop.GRM_RESERVE, 0x08, count.value, func, pos)

def builtin_industry_type(name, args, pos):
    """
    industry_type(IND_TYPE_OLD | IND_TYPE_NEW, id) builtin function

    @return The industry type in the format used by grfs (industry prop 0x16 and var 0x64)
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have 2 parameters", pos)

    from nml import global_constants
    type = args[0].reduce_constant(global_constants.const_list).value
    if type not in (0, 1):
        raise generic.ScriptError("First argument of industry_type() must be IND_TYPE_OLD or IND_TYPE_NEW", pos)

    # Industry ID uses 6 bits (0 .. 5), so bit 6 is never used
    id = args[1].reduce_constant(global_constants.const_list).value
    if not 0 <= id <= 63:
        raise generic.ScriptError("Second argument 'id' of industry_type() must be in range 0..63", pos)

    return ConstantNumeric(type << 7 | id)

def builtin_trigonometric(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    if not isinstance(args[0], (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Parameter for " + name + "() must be a constant", pos)
    trigonometric_func_table = {
        'acos': math.acos,
        'asin': math.asin,
        'atan': math.atan,
        'cos': math.cos,
        'sin': math.sin,
        'tan': math.tan,
    }
    return ConstantFloat(trigonometric_func_table[name](args[0].value), args[0].pos)

def builtin_int(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    if not isinstance(args[0], (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Parameter for " + name + "() must be a constant", pos)
    return ConstantNumeric(int(args[0].value), args[0].pos)

def builtin_abs(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    guard = BinOp(nmlop.CMP_LT, args[0], ConstantNumeric(0), args[0].pos)
    return TernaryOp(guard, BinOp(nmlop.SUB, ConstantNumeric(0), args[0], args[0].pos), args[0], args[0].pos).reduce()
#}

function_table = {
    'min' : builtin_min,
    'max' : builtin_max,
    'date' : builtin_date,
    'day_of_year' : builtin_day_of_year,
    'bitmask' : lambda name, args, pos: BitMask(args, pos),
    'STORE_TEMP' : builtin_storage,
    'STORE_PERM' : builtin_storage,
    'LOAD_TEMP' : builtin_storage,
    'LOAD_PERM' : builtin_storage,
    'hasbit' : builtin_hasbit,
    'version_openttd' : builtin_version_openttd,
    'cargotype_available' : builtin_cargotype_available,
    'railtype_available' : builtin_railtype_available,
    'grf_current_status' : builtin_grf_status,
    'grf_future_status' : builtin_grf_status,
    'grf_order_behind' : builtin_grf_status,
    'visual_effect_and_powered' : builtin_visual_effect_and_powered,
    'str2number' : builtin_str2number,
    'cargotype' : builtin_cargotype,
    'railtype' : builtin_railtype,
    'reserve_sprites' : builtin_reserve_sprites,
    'industry_type' : builtin_industry_type,
    'int' : builtin_int,
    'abs' : builtin_abs,
    'acos' : builtin_trigonometric,
    'asin' : builtin_trigonometric,
    'atan' : builtin_trigonometric,
    'cos' : builtin_trigonometric,
    'sin' : builtin_trigonometric,
    'tan' : builtin_trigonometric,
    'UCMP' : builtin_ucmp,
    'CMP' : builtin_cmp,
    'rotate' : builtin_rotate,
}
