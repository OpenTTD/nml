import operator

class Operator(object):
    def __init__(self, act2_supports, act2_str, act2_num, actd_supports, actd_str, actd_num, returns_boolean, token, compiletime_func):
        self.act2_supports = act2_supports
        self.act2_str = act2_str
        self.act2_num = act2_num
        self.actd_supports = actd_supports
        self.actd_str = actd_str
        self.actd_num = actd_num
        self.returns_boolean = returns_boolean
        self.token = token
        self.compiletime_func = compiletime_func

    def to_string(self, expr1, expr2):
        return '(%s %s %s)' % (expr1, self.token, expr2)

ADD         = Operator( True,   r'\2+',    0,  True, r'\D+',    1, False,  '+', operator.add)
SUB         = Operator( True,   r'\2-',    1,  True, r'\D-',    2, False,  '-', operator.sub)
DIV         = Operator( True,   r'\2/',    6,  True, r'\D/',   10, False,  '/', operator.div)
MOD         = Operator( True,   r'\2%',    7,  True, r'\D%',   12, False,  '%', operator.mod)
MUL         = Operator( True,   r'\2*',   10,  True, r'\D*',    4, False,  '*', operator.mul)
AND         = Operator( True,   r'\2&',   11,  True, r'\D&',    7, False,  '&', operator.and_)
OR          = Operator( True,   r'\2|',   12,  True, r'\D|',    8, False,  '|', operator.or_)
XOR         = Operator( True,   r'\2^',   13,  True,   None, None, False,  '^', operator.xor)
CMP_EQ      = Operator( True,     None, None,  True,   None, None,  True, '==', operator.eq)
CMP_NEQ     = Operator( True,     None, None,  True,   None, None,  True, '!=', operator.ne)
CMP_LE      = Operator( True,     None, None,  True,   None, None,  True, '<=', operator.le)
CMP_GE      = Operator( True,     None, None,  True,   None, None,  True, '>=', operator.ge)
CMP_LT      = Operator( True,     None, None,  True,   None, None,  True,  '<', operator.lt)
CMP_GT      = Operator( True,     None, None,  True,   None, None,  True,  '>', operator.gt)
MIN         = Operator( True,   r'\2<',    2, False,   None, None, False, None, lambda a, b: min(a, b))
MAX         = Operator( True,   r'\2>',    3, False,   None, None, False, None, lambda a, b: max(a, b))
STO_TMP     = Operator( True, r'\2sto',   14, False,   None, None, False, None, None)
STO_PERM    = Operator( True,    r'10',   16, False,   None, None, False, None, None)
SHIFT_LEFT  = Operator(False,     None, None,  True, r'\D<<',   6, False, '<<', operator.lshift)
SHIFT_RIGHT = Operator(False,     None, None,  True,   None, None, False, '>>', operator.rshift)
HASBIT      = Operator(False,     None, None,  True,   None, None,  True, None, lambda a, b: (a & (1 << b)) != 0)
#A few operators that are generated internally but can't be directly written in nml
VAL2        = Operator( True,   r'\2r',   15, False,   None, None, False, None, lambda a, b: b)
ASSIGN      = Operator(False,     None, None,  True, r'\D=',    0, False, None, None)
SHIFT_DU    = Operator(False,     None, None,  True, r'\Du<<',  5, False, None, None)
VACT2_CMP   = Operator( True,     None,   18, False,   None, None, False, None, None)
MINU        = Operator( True,  r'\2u<',    4, False,   None, None, False, None, None)


MIN.to_string = lambda expr1, expr2: 'min(%s, %s)' % (expr1, expr2)
MAX.to_string = lambda expr1, expr2: 'max(%s, %s)' % (expr1, expr2)
STO_TMP.to_string = lambda expr1, expr2: 'STORE_TEMP(%s, %s)' % (expr1, expr2)
STO_PERM.to_string = lambda expr1, expr2: 'STORE_PERM(%s, %s)' % (expr1, expr2)
HASBIT.to_string = lambda expr1, expr2: 'hasbit(%s, %s)' % (expr1, expr2)
