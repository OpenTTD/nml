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

import re

from .array import Array
from .base_expression import ConstantFloat, ConstantNumeric, Expression, Type
from .bin_not import BinNot, Not
from .binop import BinOp
from .bitmask import BitMask
from .boolean import Boolean
from .cargo import AcceptCargo, ProduceCargo
from .functioncall import FunctionCall, GRMOp, SpecialCheck
from .functionptr import FunctionPtr
from .identifier import Identifier
from .parameter import OtherGRFParameter, Parameter, parse_string_to_dword
from .patch_variable import PatchVariable
from .special_parameter import SpecialParameter
from .spritegroup_ref import SpriteGroupRef
from .storage_op import StorageOp
from .string import String
from .string_literal import StringLiteral
from .ternaryop import TernaryOp
from .variable import Variable

is_valid_id = re.compile("[a-zA-Z_][a-zA-Z0-9_]{3}$")


def identifier_to_print(name):
    """
    Check whether the given name is a valid 4 letter identifier to print
    (for cargoes, railtypes, roadtypes and tramtypes).

    @param name: Name to check.
    @return The identifier itself, if it is a valid name, else a string literal text with the name.
    """
    if is_valid_id.match(name):
        return name
    return '"{}"'.format(name)
