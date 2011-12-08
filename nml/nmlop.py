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

import operator
from .expression.base_expression import Type, ConstantNumeric, ConstantFloat
from nml import generic

class Operator(object):
    def __init__(self,
            act2_supports = False, act2_str = None, act2_num = None,
            actd_supports = False, actd_str = None, actd_num = None,
            returns_boolean = False,
            token = None,
            compiletime_func = None,
            validate_func = None):
        self.act2_supports = act2_supports
        self.act2_str = act2_str
        self.act2_num = act2_num
        self.actd_supports = actd_supports
        self.actd_str = actd_str
        self.actd_num = actd_num
        self.returns_boolean = returns_boolean
        self.token = token
        self.compiletime_func = compiletime_func
        self.validate_func = validate_func

    def to_string(self, expr1, expr2):
        return '(%s %s %s)' % (expr1, self.token, expr2)

def unsigned_rshift(a, b):
    if a < 0:
        a += 0x100000000
    return generic.truncate_int32(a >> b)

def unsigned_rrotate(a, b):
    if a < 0:
        a += 0x100000000
    return generic.truncate_int32((a >> b) | (a << (32 - b)))

def validate_func_int(expr1, expr2, pos):
    if expr1.type() != Type.INTEGER or expr2.type() != Type.INTEGER:
        raise generic.ScriptError("Binary operator requires both operands to be integers.", pos)

def validate_func_float(expr1, expr2, pos):
    if expr1.type() not in (Type.INTEGER, Type.FLOAT) or expr2.type() not in (Type.INTEGER, Type.FLOAT):
        raise generic.ScriptError("Binary operator requires both operands to be integers or floats.", pos)
    # If one is a float, the other must be constant since we can't handle floats at runtime
    if (expr1.type() == Type.FLOAT and not isinstance(expr2, (ConstantNumeric, ConstantFloat))) or \
            (expr2.type() == Type.FLOAT and not isinstance(expr1, (ConstantNumeric, ConstantFloat))):
        raise generic.ScriptError("Floating-point operations are only possible when both operands are compile-time constants.", pos)

def validate_func_add(expr1, expr2, pos):
    if (expr1.type() == Type.STRING_LITERAL) ^ (expr2.type() == Type.STRING_LITERAL):
        raise generic.ScriptError("Concatenating a string literal and a number is not possible.", pos)
    if expr1.type() != Type.STRING_LITERAL:
        validate_func_float(expr1, expr2, pos)

def validate_func_div_mod(expr1, expr2, pos):
    validate_func_float(expr1, expr2, pos)
    if isinstance(expr2, (ConstantNumeric, ConstantFloat)) and expr2.value == 0:
        raise generic.ScriptError("Division and modulo require the right hand side to be nonzero.", pos)

def validate_func_rhs_positive(expr1, expr2, pos):
    validate_func_int(expr1, expr2, pos)
    if isinstance(expr2, ConstantNumeric) and expr2.value < 0:
        raise generic.ScriptError("Right hand side of the operator may not be a negative number.", pos)

ADD = Operator(
    act2_supports = True, act2_str = r'\2+', act2_num = 0,
    actd_supports = True, actd_str = r'\D+', actd_num = 1,
    token = '+',
    compiletime_func = operator.add,
    validate_func = validate_func_add,
)

SUB = Operator(
    act2_supports = True, act2_str = r'\2-', act2_num = 1,
    actd_supports = True, actd_str = r'\D-', actd_num = 2,
    token = '-',
    compiletime_func = operator.sub,
    validate_func = validate_func_float,
)

DIV = Operator(
    act2_supports = True, act2_str = r'\2/', act2_num = 6,
    actd_supports = True, actd_str = r'\D/', actd_num = 10,
    token = '/',
    compiletime_func = lambda a, b: a // b if isinstance(a, int) and isinstance(b, int) else a / b,
    validate_func = validate_func_div_mod,
)

MOD = Operator(
    act2_supports = True, act2_str = r'\2%', act2_num = 7,
    actd_supports = True, actd_str = r'\D%', actd_num = 12,
    token = '%',
    compiletime_func = operator.mod,
    validate_func = validate_func_div_mod,
)

MUL = Operator(
    act2_supports = True, act2_str = r'\2*', act2_num = 10,
    actd_supports = True, actd_str = r'\D*', actd_num = 4,
    token = '*',
    compiletime_func = operator.mul,
    validate_func = validate_func_float,
)

AND = Operator(
    act2_supports = True, act2_str = r'\2&', act2_num = 11,
    actd_supports = True, actd_str = r'\D&', actd_num = 7,
    token = '&',
    compiletime_func = operator.and_,
    validate_func = validate_func_int,
)

OR = Operator(
    act2_supports = True, act2_str = r'\2|', act2_num = 12,
    actd_supports = True, actd_str = r'\D|', actd_num = 8,
    token = '|',
    compiletime_func = operator.or_,
    validate_func = validate_func_int,
)

XOR = Operator(
    act2_supports = True, act2_str = r'\2^', act2_num = 13,
    actd_supports = True,
    token = '^',
    compiletime_func = operator.xor,
    validate_func = validate_func_int,
)

CMP_EQ = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '==',
    compiletime_func = operator.eq,
    validate_func = validate_func_float,
)

CMP_NEQ = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '!=',
    compiletime_func = operator.ne,
    validate_func = validate_func_float,
)

CMP_LE = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '<=',
    compiletime_func = operator.le,
    validate_func = validate_func_float,
)

CMP_GE = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '>=',
    compiletime_func = operator.ge,
    validate_func = validate_func_float,
)

CMP_LT = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '<',
    compiletime_func = operator.lt,
    validate_func = validate_func_float,
)

CMP_GT = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '>',
    compiletime_func = operator.gt,
    validate_func = validate_func_float,
)

MIN = Operator(
    act2_supports = True, act2_str = r'\2<', act2_num = 2,
    actd_supports = True,
    compiletime_func = lambda a, b: min(a, b),
    validate_func = validate_func_float,
)

MAX = Operator(
    act2_supports = True, act2_str = r'\2>', act2_num = 3,
    actd_supports = True,
    compiletime_func = lambda a, b: max(a, b),
    validate_func = validate_func_float,
)

STO_TMP = Operator(
    act2_supports = True, act2_str = r'\2sto', act2_num = 14,
    validate_func = validate_func_rhs_positive,
)

STO_PERM = Operator(
    act2_supports = True, act2_str = r'\2psto', act2_num = 16,
    validate_func = validate_func_rhs_positive,
)

SHIFT_LEFT = Operator(
    act2_supports = True, act2_str = r'\2<<', act2_num = 20,
    actd_supports = True, actd_str = r'\D<<', actd_num = 6,
    token = '<<',
    compiletime_func = operator.lshift,
    validate_func = validate_func_rhs_positive,
)

SHIFT_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2>>', act2_num = 22,
    actd_supports = True,
    token = '>>',
    compiletime_func = operator.rshift,
    validate_func = validate_func_rhs_positive,
)

SHIFTU_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2u>>', act2_num = 21,
    actd_supports = True,
    token = '>>>',
    compiletime_func = unsigned_rshift,
    validate_func = validate_func_rhs_positive,
)

HASBIT = Operator(
    act2_supports = True,
    actd_supports = True,
    returns_boolean = True,
    compiletime_func = lambda a, b: (a & (1 << b)) != 0,
    validate_func = validate_func_rhs_positive,
)

#A few operators that are generated internally but can't be directly written in nml
NOTHASBIT = Operator(
    act2_supports = True,
    actd_supports = True,
    returns_boolean = True,
    compiletime_func = lambda a, b: (a & (1 << b)) == 0,
)

VAL2 = Operator(
    act2_supports = True, act2_str = r'\2r', act2_num = 15,
    compiletime_func = lambda a, b: b,
)

ASSIGN = Operator(
    actd_supports = True, actd_str = r'\D=', actd_num = 0,
)

SHIFTU_LEFT = Operator(
    actd_supports = True, actd_str = r'\Du<<', actd_num = 5,
    token = '<<',
)

VACT2_CMP = Operator(
    act2_supports = True, act2_str = r'\2cmp', act2_num = 18,
)

VACT2_UCMP = Operator(
    act2_supports = True, act2_str = r'\2ucmp', act2_num = 19,
)

MINU = Operator(
    act2_supports = True, act2_str = r'\2u<', act2_num = 4,
)

ROT_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2ror', act2_num = 17,
    compiletime_func = unsigned_rrotate,
    validate_func = validate_func_int,
)

DIVU = Operator(
    act2_supports = True, act2_str = r'\2u/', act2_num = 8,
    actd_supports = True, actd_str = r'\Du/', actd_num = 9,
)


MIN.to_string = lambda expr1, expr2: 'min(%s, %s)' % (expr1, expr2)
MAX.to_string = lambda expr1, expr2: 'max(%s, %s)' % (expr1, expr2)
STO_TMP.to_string = lambda expr1, expr2: 'STORE_TEMP(%s, %s)' % (expr1, expr2)
STO_PERM.to_string = lambda expr1, expr2: 'STORE_PERM(%s, %s)' % (expr1, expr2)
HASBIT.to_string = lambda expr1, expr2: 'hasbit(%s, %s)' % (expr1, expr2)
NOTHASBIT.to_string = lambda expr1, expr2: '!hasbit(%s, %s)' % (expr1, expr2)
VACT2_CMP.to_string = lambda expr1, expr2: 'CMP(%s, %s)' % (expr1, expr2)
VACT2_UCMP.to_string = lambda expr1, expr2: 'UCMP(%s, %s)' % (expr1, expr2)
ROT_RIGHT.to_string = lambda expr1, expr2: 'rotate(%s, %s)' % (expr1, expr2)



class GRMOperator(object):
    def __init__(self, op_str, op_num):
        self.op_str = op_str
        self.op_num = op_num
        self.value = op_num

    def __str__(self):
        return self.op_str

    def write(self, file, size):
        assert size == 1
        file.print_bytex(self.op_num, self.op_str)

GRM_RESERVE = GRMOperator(r'\DR', 0)
