__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

import calendar
import datetime
import math
from functools import reduce

from nml import generic, global_constants, nmlop

from . import identifier
from .base_expression import ConstantFloat, ConstantNumeric, Expression, Type
from .bitmask import BitMask
from .cargo import AcceptCargo, ProduceCargo
from .parameter import parse_string_to_dword
from .storage_op import StorageOp
from .string_literal import StringLiteral
from .ternaryop import TernaryOp


class FunctionCall(Expression):
    def __init__(self, name, params, pos):
        Expression.__init__(self, pos)
        self.name = name
        self.params = params

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Call function: " + self.name.value)
        for param in self.params:
            generic.print_dbg(indentation + 2, "Parameter:")
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = "{}({})".format(self.name, ", ".join(str(param) for param in self.params))
        return ret

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        # At this point we don't care about invalid arguments, they'll be handled later.
        identifier.ignore_all_invalid_ids = True
        params = [param.reduce(id_dicts, unknown_id_fatal=False) for param in self.params]
        identifier.ignore_all_invalid_ids = False
        if self.name.value in function_table:
            func = function_table[self.name.value]
            val = func(self.name.value, params, self.pos)
            return val.reduce(id_dicts)
        else:
            # try user-defined functions
            func_ptr = self.name.reduce(id_dicts, unknown_id_fatal=False, search_func_ptr=True)
            if func_ptr != self.name:  # we found something!
                if func_ptr.type() == Type.SPRITEGROUP_REF:
                    func_ptr.param_list = params
                    func_ptr.is_procedure = True
                    return func_ptr
                if func_ptr.type() != Type.FUNCTION_PTR:
                    raise generic.ScriptError(
                        "'{}' is defined, but it is not a function.".format(self.name.value), self.pos
                    )
                return func_ptr.call(params)
            if unknown_id_fatal:
                raise generic.ScriptError("'{}' is not defined as a function.".format(self.name.value), self.pos)
            return FunctionCall(self.name, params, self.pos)


class SpecialCheck(Expression):
    """
    Action7/9 special check (e.g. to see whether a cargo is defined)

    @ivar op: Action7/9 operator to use
    @type op: (C{int}, C{str})-tuple

    @ivar varnum: Variable number to read
    @type varnum: C{int}

    @ivar results: Result of the check when skipping (0) or not skipping (1)
    @type results: (C{int}, C{int})-tuple

    @ivar value: Value to test
    @type value: C{int}

    @ivar varsize: Varsize for the action7/9 check
    @type varsize: C{int}

    @ivar mask: Mask to to test only certain bits of the value
    @type mask: C{int}

    @ivar pos: Position information
    @type pos: L{Position}
    """

    def __init__(self, op, varnum, results, value, to_string, varsize=4, mask=None, pos=None):
        Expression.__init__(self, pos)
        self.op = op
        self.varnum = varnum
        self.results = results
        self.value = value
        self.to_string = to_string
        self.varsize = varsize
        self.mask = mask

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def __str__(self):
        return self.to_string

    def supported_by_actionD(self, raise_error):
        return True


class GRMOp(Expression):
    def __init__(self, op, feature, count, to_string, pos=None):
        Expression.__init__(self, pos)
        self.op = op
        self.feature = feature
        self.count = count
        self.to_string = to_string

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def __str__(self):
        return self.to_string(self)

    def supported_by_actionD(self, raise_error):
        return True


function_table = {}


def builtin(func):
    """
    Decorator that adds a function named `builtin_func` to the function table as `func`.
    """
    assert func.__name__.startswith("builtin_")
    name = func.__name__[8:]  # Strip the "builtin_". str.removeprefix() is only added in py3.9.
    function_table[name] = func
    return func


def builtins(*names):
    """
    Decorator that adds a function to the function table with one or more custom names.
    """

    def dec(func):
        for name in names:
            function_table[name] = func
        return func

    return dec


# { Builtin functions


@builtin
def builtin_min(name, args, pos):
    """
    min(...) builtin function.

    @return Lowest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("min() requires at least 2 arguments", pos)
    return reduce(lambda x, y: nmlop.MIN(x, y, pos), args)


@builtin
def builtin_max(name, args, pos):
    """
    max(...) builtin function.

    @return Heighest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("max() requires at least 2 arguments", pos)
    return reduce(lambda x, y: nmlop.MAX(x, y, pos), args)


@builtin
def builtin_date(name, args, pos):
    """
    date(year, month, day) builtin function.

    @return Days since 1 jan 1 of the given date.
    """
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if len(args) != 3:
        raise generic.ScriptError("date() requires exactly 3 arguments", pos)
    identifier.ignore_all_invalid_ids = True
    year = args[0].reduce(global_constants.const_list)
    identifier.ignore_all_invalid_ids = False
    try:
        month = args[1].reduce_constant().value
        day = args[2].reduce_constant().value
    except generic.ConstError:
        raise generic.ScriptError("Month and day parameters of date() should be compile-time constants", pos)
    generic.check_range(month, 1, 12, "month", args[1].pos)
    generic.check_range(day, 1, days_in_month[month - 1], "day", args[2].pos)

    if not isinstance(year, ConstantNumeric):
        if month != 1 or day != 1:
            raise generic.ScriptError(
                "when the year parameter of date() is not a compile time constant month and day should be 1", pos
            )
        # num_days = year*365 + year/4 - year/100 + year/400
        part1 = nmlop.MUL(year, 365)
        part2 = nmlop.DIV(year, 4)
        part3 = nmlop.DIV(year, 100)
        part4 = nmlop.DIV(year, 400)
        res = nmlop.ADD(part1, part2)
        res = nmlop.SUB(res, part3)
        res = nmlop.ADD(res, part4)
        return res

    generic.check_range(year.value, 0, 5000000, "year", year.pos)
    day_in_year = 0
    for i in range(month - 1):
        day_in_year += days_in_month[i]
    day_in_year += day
    if month >= 3 and (year.value % 4 == 0) and ((not year.value % 100 == 0) or (year.value % 400 == 0)):
        day_in_year += 1
    return ConstantNumeric(year.value * 365 + calendar.leapdays(0, year.value) + day_in_year - 1, pos)


@builtin
def builtin_day_of_year(name, args, pos):
    """
    day_of_year(month, day) builtin function.

    @return Day of the year, assuming February has 28 days.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have a month and a day parameter", pos)

    month = args[0].reduce()
    if not isinstance(month, ConstantNumeric):
        raise generic.ScriptError("Month should be a compile-time constant.", month.pos)
    if month.value < 1 or month.value > 12:
        raise generic.ScriptError("Month should be a value between 1 and 12.", month.pos)

    day = args[1].reduce()
    if not isinstance(day, ConstantNumeric):
        raise generic.ScriptError("Day should be a compile-time constant.", day.pos)

    # Mapping of month to number of days in that month.
    number_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if day.value < 1 or day.value > number_days[month.value]:
        raise generic.ScriptError("Day should be value between 1 and {:d}.".format(number_days[month.value]), day.pos)

    return ConstantNumeric(datetime.date(1, month.value, day.value).toordinal(), pos)


@builtins("STORE_TEMP", "STORE_PERM", "LOAD_TEMP", "LOAD_PERM")
def builtin_storage(name, args, pos):
    """
    Accesses to temporary / persistent storage
    """
    return StorageOp(name, args, pos)


@builtin
def builtin_UCMP(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return nmlop.VACT2_UCMP(args[0], args[1], pos)


@builtin
def builtin_CMP(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return nmlop.VACT2_CMP(args[0], args[1], pos)


@builtin
def builtin_rotate(name, args, pos):
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return nmlop.ROT_RIGHT(args[0], args[1], pos)


@builtin
def builtin_bitmask(name, args, pos):
    return BitMask(args, pos)


@builtin
def builtin_hasbit(name, args, pos):
    """
    hasbit(value, bit_num) builtin function.

    @return C{1} if and only if C{value} has bit C{bit_num} set, C{0} otherwise.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return nmlop.HASBIT(args[0], args[1], pos)


@builtin
def builtin_getbits(name, args, pos):
    """
    getbits(value, first, amount) builtin function.

    @return Extract C{amount} bits starting at C{first} from C{value},
            that is (C{value} >> C{first}) & (1 << C{amount} - 1)
    """
    if len(args) != 3:
        raise generic.ScriptError(name + "() must have exactly three parameters", pos)

    # getbits(value, first, amount) = (value >> first) & ((0xFFFFFFFF << amount) ^ 0xFFFFFFFF)
    part1 = nmlop.SHIFTU_RIGHT(args[0], args[1], pos)
    part2 = nmlop.SHIFT_LEFT(0xFFFFFFFF, args[2], pos)
    part3 = nmlop.XOR(part2, 0xFFFFFFFF, pos)

    return nmlop.AND(part1, part3, pos)


@builtin
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


@builtins("cargotype_available", "railtype_available", "roadtype_available", "tramtype_available")
def builtin_typelabel_available(name, args, pos):
    """
    {cargo|rail|road|tram}type_available(label) builtin functions.

    @return 1 if the label is available, 0 otherwise.
    """
    op = {
        "cargotype_available": (0x0B, r"\7c"),
        "railtype_available": (0x0D, None),
        "roadtype_available": (0x0F, None),
        "tramtype_available": (0x11, None),
    }[name]

    if len(args) != 1:
        raise generic.ScriptError(name + "() must have exactly 1 parameter", pos)
    label = args[0].reduce()
    return SpecialCheck(op, 0, (0, 1), parse_string_to_dword(label), "{}({})".format(name, label), pos=args[0].pos)


@builtins("grf_current_status", "grf_future_status", "grf_order_behind")
def builtin_grf_status(name, args, pos):
    """
    grf_{current_status|future_status|order_behind}(grfid[, mask]) builtin functions.

    @return 1 if the grf is, or will be, active, 0 otherwise.
    """
    op, results = {
        # can't use \7g (0, 1), because that's false when the queried grf isn't present at all.
        "grf_current_status": ((0x06, r"\7G"), (1, 0)),
        "grf_future_status": ((0x0A, r"\7gg"), (0, 1)),
        "grf_order_behind": ((0x08, r"\7gG"), (0, 1)),
    }[name]

    if len(args) == 1:
        grfid = args[0].reduce()
        mask = None
        string = "{}({})".format(name, grfid)
        varsize = 4
    elif len(args) == 2:
        grfid = args[0].reduce()
        mask = parse_string_to_dword(args[1].reduce())
        string = "{}({}, {})".format(name, grfid, mask)
        varsize = 8
    else:
        raise generic.ScriptError(name + "() must have 1 or 2 parameters", pos)

    return SpecialCheck(op, 0x88, results, parse_string_to_dword(grfid), string, varsize, mask, args[0].pos)


@builtins("visual_effect", "visual_effect_and_powered")
def builtin_visual_effect_and_powered(name, args, pos):
    """
    Builtin function, used in two forms:
    visual_effect_and_powered(effect, offset, powered)
    visual_effect(effect, offset)
    Use this to set the vehicle property visual_effect[_and_powered]
    and for the callback VEH_CB_VISUAL_EFFECT[_AND_POWERED]

    """
    arg_len = 2 if name == "visual_effect" else 3
    if len(args) != arg_len:
        raise generic.ScriptError(name + "() must have {:d} parameters".format(arg_len), pos)
    effect = args[0].reduce_constant(global_constants.const_list).value
    offset = nmlop.ADD(args[1], 8).reduce_constant().value
    generic.check_range(offset, 0, 0x0F, "offset in function " + name, pos)
    if arg_len == 3:
        powered = args[2].reduce_constant(global_constants.const_list).value
        if powered != 0 and powered != 0x80:
            raise generic.ScriptError(
                "3rd argument to visual_effect_and_powered (powered) must be"
                " either ENABLE_WAGON_POWER or DISABLE_WAGON_POWER",
                pos,
            )
    else:
        powered = 0
    return ConstantNumeric(effect | offset | powered)


@builtin
def builtin_create_effect(name, args, pos):
    """
    Builtin function:
    create_effect(effect_sprite, l_x_offset, t_y_offset, z_offset)
    Use this to set the values for temporary storages 100+x
    in the callback create_effect

    """
    if len(args) != 4:
        raise generic.ScriptError(name + "() must have 4 parameters", pos)

    sprite = args[0].reduce_constant(global_constants.const_list).value
    offset1 = args[1].reduce_constant().value
    offset2 = args[2].reduce_constant().value
    offset3 = args[3].reduce_constant().value

    generic.check_range(sprite, 0, 255, "effect_sprite in function " + name, args[0].pos)
    generic.check_range(offset1, -128, 127, "l_x_offset in function " + name, args[1].pos)
    generic.check_range(offset2, -128, 127, "t_y_offset in function " + name, args[2].pos)
    generic.check_range(offset3, -128, 127, "z_offset in function " + name, args[3].pos)

    return ConstantNumeric(sprite | (offset1 & 0xFF) << 8 | (offset2 & 0xFF) << 16 | (offset3 & 0xFF) << 24)


@builtin
def builtin_str2number(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    return ConstantNumeric(parse_string_to_dword(args[0]))


@builtins("cargotype", "railtype", "roadtype", "tramtype")
def builtin_resolve_typelabel(name, args, pos, table_name=None):
    """
    {cargo,rail,road,tram}type(label) builtin functions.

    Also used from some Action2Var variables to resolve cargo labels.
    """
    tracktype_funcs = {
        "cargotype": global_constants.cargo_numbers,
        "railtype": global_constants.railtype_table,
        "roadtype": global_constants.roadtype_table,
        "tramtype": global_constants.tramtype_table,
    }

    if not table_name:
        table_name = name
    table = tracktype_funcs[table_name]
    if table_name == "cargotype":
        table_name = "cargo"  # NML syntax uses "cargotable" and "railtypetable"

    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    if not isinstance(args[0], StringLiteral) or args[0].value not in table:
        raise generic.ScriptError(
            "Parameter for {}() must be a string literal that is also in your {} table".format(name, table_name), pos
        )
    return ConstantNumeric(table[args[0].value])


@builtin
def builtin_reserve_sprites(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    count = args[0].reduce_constant()
    return GRMOp(nmlop.GRM_RESERVE, 0x08, count.value, lambda x: "{}({:d})".format(name, count.value), pos)


@builtin
def builtin_industry_type(name, args, pos):
    """
    industry_type(IND_TYPE_OLD | IND_TYPE_NEW, id) builtin function

    @return The industry type in the format used by grfs (industry prop 0x16 and var 0x64)
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have 2 parameters", pos)

    type = args[0].reduce_constant(global_constants.const_list).value
    if type not in (0, 1):
        raise generic.ScriptError("First argument of industry_type() must be IND_TYPE_OLD or IND_TYPE_NEW", pos)

    # Industry ID uses 7 bits (0 .. 6), bit 7 is for old/new
    id = args[1].reduce_constant(global_constants.const_list).value
    if not 0 <= id <= 127:
        raise generic.ScriptError("Second argument 'id' of industry_type() must be in range 0..127", pos)

    return ConstantNumeric(type << 7 | id)


@builtins("accept_cargo", "produce_cargo")
def builtin_cargoexpr(name, args, pos):
    if len(args) < 1:
        raise generic.ScriptError(name + "() must have 1 or more parameters", pos)

    if not isinstance(args[0], StringLiteral) or args[0].value not in global_constants.cargo_numbers:
        raise generic.ScriptError(
            "First argument of " + name + "() must be a string literal that is also in your cargo table", pos
        )
    cargotype = global_constants.cargo_numbers[args[0].value]

    if name == "produce_cargo":
        return ProduceCargo(cargotype, args[1:], pos)
    elif name == "accept_cargo":
        return AcceptCargo(cargotype, args[1:], pos)
    else:
        raise AssertionError()


@builtins("acos", "asin", "atan", "cos", "sin", "sqrt", "tan")
def builtin_math(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    val = args[0].reduce()
    if not isinstance(val, (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Parameter for " + name + "() must be a constant", pos)
    math_func_table = {
        "acos": math.acos,
        "asin": math.asin,
        "atan": math.atan,
        "cos": math.cos,
        "sin": math.sin,
        "sqrt": math.sqrt,
        "tan": math.tan,
    }
    return ConstantFloat(math_func_table[name](val.value), val.pos)


@builtin
def builtin_round(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    val = args[0].reduce()
    if not isinstance(val, (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Parameter for " + name + "() must be a constant", pos)
    return ConstantNumeric(round(val.value), pos)


@builtin
def builtin_int(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    val = args[0].reduce()
    if not isinstance(val, (ConstantNumeric, ConstantFloat)):
        raise generic.ScriptError("Parameter for " + name + "() must be a constant", pos)
    return ConstantNumeric(int(val.value), val.pos)


@builtin
def builtin_abs(name, args, pos):
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)
    guard = nmlop.CMP_LT(args[0], 0)
    return TernaryOp(guard, nmlop.SUB(0, args[0]), args[0], args[0].pos).reduce()


@builtin
def builtin_sound(name, args, pos):
    if len(args) not in (1, 2):
        raise generic.ScriptError(name + "() must have 1 or 2 parameters", pos)
    if not isinstance(args[0], StringLiteral):
        raise generic.ScriptError("Parameter for " + name + "() must be a string literal", pos)
    volume = args[1].reduce_constant().value if len(args) >= 2 else 100
    generic.check_range(volume, 0, 100, "sound volume", pos)
    from nml.actions import action11

    return ConstantNumeric(action11.add_sound((args[0].value, volume), pos), pos)


@builtin
def builtin_import_sound(name, args, pos):
    if len(args) not in (2, 3):
        raise generic.ScriptError(name + "() must have 2 or 3 parameters", pos)
    grfid = parse_string_to_dword(args[0].reduce())
    sound_num = args[1].reduce_constant().value
    volume = args[2].reduce_constant().value if len(args) >= 3 else 100
    generic.check_range(volume, 0, 100, "sound volume", pos)
    from nml.actions import action11

    return ConstantNumeric(action11.add_sound((grfid, sound_num, volume), pos), pos)


@builtin
def builtin_relative_coord(name, args, pos):
    """
    relative_coord(x, y) builtin function.

    @return Coordinates in 0xYYXX format.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have x and y coordinates as parameters", pos)

    if isinstance(args[0], ConstantNumeric):
        generic.check_range(args[0].value, 0, 255, "Argument of '{}'".format(name), args[0].pos)
    if isinstance(args[1], ConstantNumeric):
        generic.check_range(args[1].value, 0, 255, "Argument of '{}'".format(name), args[1].pos)

    x_coord = nmlop.AND(args[0], 0xFF)
    y_coord = nmlop.AND(args[1], 0xFF)
    # Shift Y to its position.
    y_coord = nmlop.SHIFT_LEFT(y_coord, 8)

    return nmlop.OR(x_coord, y_coord, pos)


@builtin
def builtin_num_corners_raised(name, args, pos):
    """
    num_corners_raised(slope) builtin function.
    slope is a 5-bit value

    @return Number of raised corners in a slope (4 for steep slopes)
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)

    slope = args[0]
    # The returned value is ((slope x 0x8421) & 0x11111) % 0xF
    # Explanation in steps: (numbers in binary)
    # - Masking constrains the slope to 5 bits, just to be sure (a|bcde)
    # - Multiplication creates 4 copies of those bits (abcd|eabc|deab|cdea|bcde)
    # - And-masking leaves only the lowest bit in each nibble (000d|000c|000b|000a|000e)
    # - The modulus operation adds one to the output for each set bit
    # - We now have the count of bits in the slope, which is wat we want. yay!
    slope = nmlop.AND(slope, 0x1F, pos)
    slope = nmlop.MUL(slope, 0x8421)
    slope = nmlop.AND(slope, 0x11111)
    return nmlop.MOD(slope, 0xF)


@builtin
def builtin_slope_to_sprite_offset(name, args, pos):
    """
    builtin function slope_to_sprite_offset(slope)

    @return sprite offset to use
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)

    if isinstance(args[0], ConstantNumeric):
        generic.check_range(args[0].value, 0, 15, "Argument of '{}'".format(name), args[0].pos)

    # step 1: ((slope >= 0) & (slope <= 14)) * slope
    # This handles all non-steep slopes
    expr = nmlop.AND(nmlop.CMP_LE(args[0], 14, pos), nmlop.CMP_GE(args[0], 0, pos))
    expr = nmlop.MUL(expr, args[0])
    # Now handle the steep slopes separately
    # So add (slope == SLOPE_XX) * offset_of_SLOPE_XX for each steep slope
    steep_slopes = [(23, 16), (27, 17), (29, 15), (30, 18)]
    for slope, offset in steep_slopes:
        to_add = nmlop.MUL(nmlop.CMP_EQ(args[0], slope, pos), offset)
        expr = nmlop.ADD(expr, to_add)
    return expr


@builtin
def builtin_palette_1cc(name, args, pos):
    """
    palette_1cc(colour) builtin function.

    @return Recolour sprite to use
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have 1 parameter", pos)

    if isinstance(args[0], ConstantNumeric):
        generic.check_range(args[0].value, 0, 15, "Argument of '{}'".format(name), args[0].pos)

    return nmlop.ADD(args[0], 775, pos)


@builtin
def builtin_palette_2cc(name, args, pos):
    """
    palette_2cc(colour1, colour2) builtin function.

    @return Recolour sprite to use
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have 2 parameters", pos)

    for i in range(0, 2):
        if isinstance(args[i], ConstantNumeric):
            generic.check_range(args[i].value, 0, 15, "Argument of '{}'".format(name), args[i].pos)

    col2 = nmlop.MUL(args[1], 16, pos)
    col12 = nmlop.ADD(col2, args[0])
    # Base sprite is not a constant
    base = global_constants.patch_variable("base_sprite_2cc", global_constants.patch_variables["base_sprite_2cc"], pos)

    return nmlop.ADD(col12, base)


@builtin
def builtin_vehicle_curv_info(name, args, pos):
    """
    vehicle_curv_info(prev_cur, cur_next) builtin function

    @return Value to use with vehicle var curv_info
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have 2 parameters", pos)

    for arg in args:
        if isinstance(arg, ConstantNumeric):
            generic.check_range(arg.value, -2, 2, "Argument of '{}'".format(name), arg.pos)

    args = [nmlop.AND(arg, 0xF, pos) for arg in args]
    cur_next = nmlop.SHIFT_LEFT(args[1], 8)
    return nmlop.OR(args[0], cur_next)


@builtin
def builtin_format_string(name, args, pos):
    """
    format_string(format, ... args ..) builtin function

    @return Formatted string
    """
    if len(args) < 1:
        raise generic.ScriptError(name + "() must have at least one parameter", pos)

    format = args[0].reduce()
    if not isinstance(format, StringLiteral):
        raise generic.ScriptError(name + "() parameter 1 'format' must be a literal string", format.pos)

    # Validate other args
    format_args = []
    for i, arg in enumerate(args[1:]):
        arg = arg.reduce()
        if not isinstance(arg, (StringLiteral, ConstantFloat, ConstantNumeric)):
            raise generic.ScriptError(
                name + "() parameter {:d} is not a constant number of literal string".format(i + 1), arg.pos
            )
        format_args.append(arg.value)

    try:
        result = format.value % tuple(format_args)
        return StringLiteral(result, pos)
    except Exception as ex:
        raise generic.ScriptError("Invalid combination of format / arguments for {}: {}".format(name, str(ex)), pos)


# }
