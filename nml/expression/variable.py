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
        self.extra_params = []

    def debug_print(self, indentation):
        print indentation*' ' + 'Action2 variable'
        self.num.debug_print(indentation + 2)
        if self.param is not None:
            print (indentation+2)*' ' + 'Parameter:'
            if isinstance(self.param, basestring):
                print (indentation+4)*' ' + 'Procedure call:', self.param
            else:
                self.param.debug_print(indentation + 4)
            if len(self.extra_params) > 0: print (indentation+2)*' ' + 'Extra parameters:'
            for extra_param in self.extra_params:
                extra_param.debug_print(indentation + 4)

    def __str__(self):
        num = "0x%02X" % self.num.value if isinstance(self.num, ConstantNumeric) else str(self.num)
        ret = 'var[%s, %s, %s' % (num, str(self.shift), str(self.mask))
        if self.param is not None:
            ret += ', %s' % str(self.param)
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
        if not all(map(lambda x: x.type() == Type.INTEGER, (num, shift, mask))) or \
                (param is not None and param.type() != Type.INTEGER):
            raise generic.ScriptError("All parts of a variable access must be integers.", self.pos)
        var = Variable(num, shift, mask, param, self.pos)
        var.add = None if self.add is None else self.add.reduce(id_dicts)
        var.div = None if self.div is None else self.div.reduce(id_dicts)
        var.mod = None if self.mod is None else self.mod.reduce(id_dicts)
        var.extra_params = [(extra_param[0], extra_param[1].reduce(id_dicts)) for extra_param in self.extra_params]
        return var

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        if raise_error:
            if isinstance(self.num, ConstantNumeric):
                if self.num.value == 0x7C: raise generic.ScriptError("LOAD_PERM is only available in switch-blocks.", self.pos)
                if self.num.value == 0x7D: raise generic.ScriptError("LOAD_TEMP is only available in switch-blocks.", self.pos)
            raise generic.ScriptError("Variable accesses are not supported outside of switch-blocks.", self.pos)
        return False
