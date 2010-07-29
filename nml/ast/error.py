from nml import generic, expression
from nml.actions import actionB

class Error(object):
    def __init__(self, param_list, pos):
        self.params = []
        self.pos = pos
        if not 2 <= len(param_list) <= 5:
            raise generic.ScriptError("'error' expects between 2 and 5 parameters, got " + str(len(param_list)), self.pos)
        self.severity = param_list[0].reduce([actionB.error_severity])
        self.msg      = param_list[1]
        self.data     = param_list[2] if len(param_list) >= 3 else None
        self.params.append(param_list[3].reduce() if len(param_list) >= 4 else None)
        self.params.append(param_list[4].reduce() if len(param_list) >= 5 else None)

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Error message'
        print (indentation+2)*' ' + 'Message:'
        self.msg.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Severity:'
        self.severity.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Data: '
        if self.data is not None: self.data.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Param1: '
        if self.params[0] is not None: self.params[0].debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Param2: '
        if self.params[1] is not None: self.params[1].debug_print(indentation + 4)

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
        if self.params[0] is not None:
            res += ', %s' % self.params[0]
        if self.params[1] is not None:
            res += ', %s' % self.params[1]
        res += ');\n'
        return res
