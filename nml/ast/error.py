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

from nml import generic, expression
from nml.actions import actionB
from nml.ast import base_statement

class Error(base_statement.BaseStatement):
    """
    An error has occured while parsing the GRF. This can be anything ranging from
    an imcompatible GRF file that was found or a game setting that is set to the
    wrong value to a wrong combination of parameters. The action taken by the host
    depends on the severity level of the error.
    NML equivalent: error(level, message[, extra_text[, parameter1[, parameter2]]]).

    @ivar params: Extra expressions whose value can be used in the error string.
    @type params: C{list} of L{Expression}

    @ivar severity: Severity level of this error, value between 0 and 3.
    @type severity: L{Expression}

    @ivar msg: The string to be used for this error message. This can be either
               one of the predifined error strings or a custom string from the
               language file.
    @type msg: L{Expression}

    @ivar data: Optional extra message that is inserted in place of the second
                {STRING}-code of msg.
    @type data: C{None} or L{String} or L{StringLiteral}
    """
    def __init__(self, param_list, pos):
        base_statement.BaseStatement.__init__(self, "error()", pos)
        if not 2 <= len(param_list) <= 5:
            raise generic.ScriptError("'error' expects between 2 and 5 parameters, got " + str(len(param_list)), self.pos)
        self.severity = param_list[0]
        self.msg      = param_list[1]
        self.data     = param_list[2] if len(param_list) >= 3 else None
        self.params = param_list[3:]

    def pre_process(self):
        self.severity = self.severity.reduce([actionB.error_severity])
        self.msg      = self.msg.reduce([actionB.default_error_msg])
        if self.data:
            self.data = self.data.reduce()
        self.params = [x.reduce() for x in self.params]

    def debug_print(self, indentation):
        print indentation*' ' + 'Error message'
        print (indentation+2)*' ' + 'Message:'
        self.msg.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Severity:'
        self.severity.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Data: '
        if self.data is not None: self.data.debug_print(indentation + 4)
        if len(self.params) > 0:
            print (indentation+2)*' ' + 'Param1: '
            self.params[0].debug_print(indentation + 4)
        if len(self.params) > 1:
            print (indentation+2)*' ' + 'Param2: '
            self.params[1].debug_print(indentation + 4)

    def get_action_list(self):
        return actionB.parse_error_block(self)

    def __str__(self):
        sev = str(self.severity)
        if isinstance(self.severity, expression.ConstantNumeric):
            for s in actionB.error_severity:
                if self.severity.value == actionB.error_severity[s]:
                    sev = s
                    break
        res = 'error(%s, %s' % (sev, self.msg)
        if self.data is not None:
            res += ', %s' % self.data
        if len(self.params) > 0:
            res += ', %s' % self.params[0]
        if len(self.params) > 1:
            res += ', %s' % self.params[1]
        res += ');\n'
        return res
