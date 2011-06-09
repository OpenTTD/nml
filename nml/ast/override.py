from nml import generic, expression, global_constants
from nml.ast import assignment
from nml.actions import action0

class EngineOverride:
    """
    AST Node for an engine override.

    @ivar grfid: GRFid of the grf to override the engines from.
    @type grfid: L{Expression}

    @ivar source_grfid: GRFid of the grf that overrides the engines.
    @type source_grfid: L{Expression} or C{None}

    @ivar pos: Position information of the engine_override block.
    @type pos: L{Position}
    """
    def __init__(self, args, pos):
        self.args = args
        self.pos = pos

    def register_names(self):
        pass

    def pre_process(self):
        if len(self.args) not in (1, 2):
            raise generic.ScriptError("engine_override expects 1 or 2 parameters", self.pos)

        if len(self.args) == 1:
            source = expression.Identifier('GRFID')
        else:
            source = self.args[0]
        self.source_grfid = source.reduce(global_constants.const_list)
        if isinstance(self.source_grfid, expression.StringLiteral):
            self.source_grfid = expression.ConstantNumeric(expression.parse_string_to_dword(self.source_grfid))

        self.grfid = self.args[-1].reduce(global_constants.const_list)
        if isinstance(self.grfid, expression.StringLiteral):
            self.grfid = expression.ConstantNumeric(expression.parse_string_to_dword(self.grfid))

    def debug_print(self, indentation):
        print indentation*' ' + 'Engine override'
        print (indentation+2)*' ' + 'Source:', str(self.source_grfid)
        print (indentation+2)*' ' + 'Target:', str(self.grfid)

    def get_action_list(self):
        return action0.get_engine_override_action(self)

    def __str__(self):
        return "engine_override(%s);\n" % ', '.join(str(x) for x in self.args)

