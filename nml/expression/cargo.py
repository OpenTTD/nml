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
from .base_expression import Expression

class ProduceCargo(Expression):
    def __init__(self, cargotype, factor, pos):
        Expression.__init__(self, pos)
        self.cargotype = cargotype
        self.factor = factor

    def debug_print(self, indentation):
        generic.print_dbg(indentation, 'Produce cargo ' + self.cargotype + " * " + self.factor)

    def __str__(self):
        return 'produce_cargo(' + self.cargotype + ', ' + self.factor + ')'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class AcceptCargo(Expression):
    def __init__(self, cargotype, outputs, pos):
        Expression.__init__(self, pos)
        self.cargotype = cargotype
        self.outputs = outputs

    def debug_print(self, indentation):
        if len(self.outputs) == 0:
            generic.print_dbg(indentation, 'Accept cargo ' + self.cargotype + ' and produce nothing')
        else:
            generic.print_dbg(indentation, 'Accept cargo ' + self.cargotype + ' and produce:')
            for output in self.outputs:
                output.debug_print(indentation + 2)

    def __str__(self):
        return 'accept_cargo(' + self.cargotype + ', [' + ', '.join(str(o) for o in self.outputs) + '])'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self
