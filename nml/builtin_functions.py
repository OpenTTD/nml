import datetime, calendar
from nml import generic
from expression import *

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
    except ConstError:
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
