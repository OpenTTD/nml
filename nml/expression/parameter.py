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

from nml import generic
from .base_expression import Type, Expression, ConstantNumeric
from .label import Label

class Parameter(Expression):
    def __init__(self, num, pos = None, by_user = False):
        Expression.__init__(self, pos)
        self.num = num
        if by_user and isinstance(num, ConstantNumeric) and not (0 <= num.value <= 63):
            generic.print_warning("Accessing parameters out of the range 0..63 is not supported and may lead to unexpected behaviour.", pos)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Parameter:')
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return 'param[{}]'.format(self.num)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        num = self.num.reduce(id_dicts)
        if num.type() != Type.INTEGER:
            raise generic.ScriptError("Parameter number must be an integer.", num.pos)
        return Parameter(num, self.pos)

    def supported_by_action2(self, raise_error):
        supported = isinstance(self.num, ConstantNumeric)
        if not supported and raise_error:
            raise generic.ScriptError("Parameter acessess with non-constant numbers are not supported in a switch-block.", self.pos)
        return supported

    def supported_by_actionD(self, raise_error):
        return True

    def __eq__(self, other):
        return other is not None and isinstance(other, Parameter) and self.num == other.num

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.num,))

class OtherGRFParameter(Expression):
    def __init__(self, grfid, num, pos = None):
        Expression.__init__(self, pos)
        self.grfid = grfid
        self.num = num

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'OtherGRFParameter:')
        self.grfid.debug_print(indentation + 2)
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return 'param[{}, {}]'.format(self.grfid, self.num)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        grfid = self.grfid.reduce(id_dicts)
        Label(grfid)  # Test validity
        num = self.num.reduce(id_dicts)
        if num.type() != Type.INTEGER:
            raise generic.ScriptError("Parameter number must be an integer.", num.pos)
        return OtherGRFParameter(grfid, num, self.pos)

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Reading parameters from another GRF is not supported in a switch-block.", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        return True
