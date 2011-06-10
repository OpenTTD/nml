import re

from .array import Array
from .base_expression import Type, Expression, ConstantNumeric, ConstantFloat
from .bin_not import BinNot, Not
from .binop import BinOp
from .bitmask import BitMask
from .boolean import Boolean
from .functioncall import FunctionCall, SpecialCheck, GRMOp
from .functionptr import FunctionPtr
from .identifier import Identifier
from .patch_variable import PatchVariable
from .parameter import Parameter, OtherGRFParameter, parse_string_to_dword
from .special_parameter import SpecialParameter
from .string import String
from .string_literal import StringLiteral
from .ternaryop import TernaryOp
from .variable import Variable

is_valid_id = re.compile('[a-zA-Z_][a-zA-Z0-9_]{3}$')

def identifier_to_print(value):
    if is_valid_id.match(value): return value
    return '"%s"' % value

