import operator
from nml import generic

class Operator(object):
    def __init__(self,
            act2_supports = False, act2_str = None, act2_num = None,
            actd_supports = False, actd_str = None, actd_num = None,
            returns_boolean = False,
            token = None,
            compiletime_func = None,
            supports_floats = False):
        self.act2_supports = act2_supports
        self.act2_str = act2_str
        self.act2_num = act2_num
        self.actd_supports = actd_supports
        self.actd_str = actd_str
        self.actd_num = actd_num
        self.returns_boolean = returns_boolean
        self.token = token
        self.compiletime_func = compiletime_func
        self.supports_floats = supports_floats

    def to_string(self, expr1, expr2):
        return '(%s %s %s)' % (expr1, self.token, expr2)

def unsigned_rshift(a, b):
    if a < 0:
        a += 0x100000000
    return generic.truncate_int32(a >> b)


ADD = Operator(
    act2_supports = True, act2_str = r'\2+', act2_num = 0,
    actd_supports = True, actd_str = r'\D+', actd_num = 1,
    token = '+',
    compiletime_func = operator.add,
    supports_floats = True
)

SUB = Operator(
    act2_supports = True, act2_str = r'\2-', act2_num = 1,
    actd_supports = True, actd_str = r'\D-', actd_num = 2,
    token = '-',
    compiletime_func = operator.sub,
    supports_floats = True
)

DIV = Operator(
    act2_supports = True, act2_str = r'\2/', act2_num = 6,
    actd_supports = True, actd_str = r'\D/', actd_num = 10,
    token = '=',
    compiletime_func = operator.div,
    supports_floats = True
)

MOD = Operator(
    act2_supports = True, act2_str = r'\2%', act2_num = 7,
    actd_supports = True, actd_str = r'\D%', actd_num = 12,
    token = '%',
    compiletime_func = operator.mod,
    supports_floats = True
)

MUL = Operator(
    act2_supports = True, act2_str = r'\2*', act2_num = 10,
    actd_supports = True, actd_str = r'\D*', actd_num = 4,
    token = '*',
    compiletime_func = operator.mul,
    supports_floats = True
)

AND = Operator(
    act2_supports = True, act2_str = r'\2&', act2_num = 11,
    actd_supports = True, actd_str = r'\D&', actd_num = 7,
    token = '&',
    compiletime_func = operator.and_
)

OR = Operator(
    act2_supports = True, act2_str = r'\2|', act2_num = 12,
    actd_supports = True, actd_str = r'\D|', actd_num = 8,
    token = '|',
    compiletime_func = operator.or_
)

XOR = Operator(
    act2_supports = True, act2_str = r'\2^', act2_num = 13,
    actd_supports = True,
    token = '^',
    compiletime_func = operator.xor
)

CMP_EQ = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '==',
    compiletime_func = operator.eq,
    supports_floats = True
)

CMP_NEQ = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '!=',
    compiletime_func = operator.ne,
    supports_floats = True
)

CMP_LE = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '<=',
    compiletime_func = operator.le,
    supports_floats = True
)

CMP_GE = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '>=',
    compiletime_func = operator.ge,
    supports_floats = True
)

CMP_LT = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '<',
    compiletime_func = operator.lt,
    supports_floats = True
)

CMP_GT = Operator(
    act2_supports = True,
    actd_supports = True,
    token = '>',
    compiletime_func = operator.gt,
    supports_floats = True
)

MIN = Operator(
    act2_supports = True, act2_str = r'\2<', act2_num = 2,
    actd_supports = True,
    compiletime_func = lambda a, b: min(a, b),
    supports_floats = True
)

MAX = Operator(
    act2_supports = True, act2_str = r'\2>', act2_num = 3,
    actd_supports = True,
    compiletime_func = lambda a, b: max(a, b),
    supports_floats = True
)

STO_TMP = Operator(
    act2_supports = True, act2_str = r'\2sto', act2_num = 14,
)

STO_PERM = Operator(
    act2_supports = True, act2_str = r'\2psto', act2_num = 16,
)

SHIFT_LEFT = Operator(
    act2_supports = True, act2_str = r'\2<<', act2_num = 20,
    actd_supports = True, actd_str = r'\D<<', actd_num = 6,
    token = '<<',
    compiletime_func = operator.lshift
)

SHIFT_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2>>', act2_num = 22,
    actd_supports = True,
    token = '>>',
    compiletime_func = operator.rshift
)

SHIFTU_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2u>>', act2_num = 21,
    actd_supports = True,
    token = '>>>',
    compiletime_func = unsigned_rshift
)

HASBIT = Operator(
    act2_supports = True,
    actd_supports = True,
    returns_boolean = True,
    compiletime_func = lambda a, b: (a & (1 << b)) != 0
)

#A few operators that are generated internally but can't be directly written in nml
NOTHASBIT = Operator(
    act2_supports = True,
    actd_supports = True,
    returns_boolean = True,
    compiletime_func = lambda a, b: (a & (1 << b)) == 0
)

VAL2 = Operator(
    act2_supports = True, act2_str = r'\2r', act2_num = 15,
    compiletime_func = lambda a, b: b
)

ASSIGN = Operator(
    actd_supports = True, actd_str = r'\D=', actd_num = 0,
)

SHIFTU_LEFT = Operator(
    actd_supports = True, actd_str = r'\Du<<', actd_num = 5,
)

VACT2_CMP = Operator(
    act2_supports = True, act2_str = r'\2cmp', act2_num = 18,
)

MINU = Operator(
    act2_supports = True, act2_str = r'\2u<', act2_num = 4,
)

ROT_RIGHT = Operator(
    act2_supports = True, act2_str = r'\2ror', act2_num = 17,
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
