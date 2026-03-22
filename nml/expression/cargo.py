# SPDX-License-Identifier: GPL-2.0-or-later

from nml import generic, global_constants

from .base_expression import Expression


class CargoExpression(Expression):
    def __init__(self, cargotype, value, pos):
        Expression.__init__(self, pos)
        assert isinstance(value, list)
        self.cargotype = cargotype
        self.value = value

    def cargolabel(self):
        for label, number in global_constants.cargo_numbers.items():
            if number == self.cargotype:
                return label
        raise AssertionError("Cargo expression with unregistered cargotype at " + str(self.pos))

    def debug_print(self, indentation):
        if self.value is None:
            generic.print_dbg(indentation, "{0} cargo {1}".format(self._debugname, self.cargolabel()))
        else:
            generic.print_dbg(indentation, "{0} cargo {1} with result:".format(self._debugname, self.cargolabel()))
            self.value.debug_print(indentation + 2)

    def __str__(self):
        return "{0}({1}, {2})".format(self._fnname, self.cargolabel(), str(self.value))

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self


class AcceptCargo(CargoExpression):
    _fnname = "accept_cargo"
    _debugname = "Accept"


class ProduceCargo(CargoExpression):
    _fnname = "produce_cargo"
    _debugname = "Produce"
