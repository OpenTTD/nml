from nml.expression import *
from nml.generic import *
from action2 import *
from action2var_variables import *
from action6 import *
from actionD import *
from nml import global_constants

class Action2Operator:
    ADD   = r'\2+'
    SUB   = r'\2-'
    MUL   = r'\2*'
    AND   = r'\2&'
    OR    = r'\2|'
    XOR   = r'\2^'
    DIVU  = r'\2u/'
    DIVS  = r'\2/'
    MODU  = r'\2u%'
    MODS  = r'\2%'
    MIN   = r'\2<'
    MAX   = r'\2>'
    VAL2  = r'\2r'
    STO_TMP = r'\2sto'

action2operator_to_num = {
    Action2Operator.ADD: 0,
    Action2Operator.SUB: 1,
    Action2Operator.MUL: 0x0A,
    Action2Operator.AND: 0x0B,
    Action2Operator.OR: 0x0C,
    Action2Operator.XOR: 0x0D,
    Action2Operator.DIVU: 8,
    Action2Operator.DIVS: 6,
    Action2Operator.MODU: 9,
    Action2Operator.MODS: 7,
    Action2Operator.MIN: 2,
    Action2Operator.MAX: 3,
    Action2Operator.VAL2: 0x0F,
    Action2Operator.STO_TMP: 0x0E,
}

class Action2Var(Action2):
    def __init__(self, feature, name, type_byte, varsize):
        Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        self.varsize = varsize
        self.tmp_locations = range(0x80, 0x100)
        self.references = []
        self.ranges = []

    def resolve_tmp_storage(self):
        self.references = set(self.references)
        for var in self.var_list:
            if isinstance(var, VarAction2StoreTempVar):
                var.mask = ConstantNumeric(self.tmp_locations.pop())
                for action2 in self.references:
                    if var.mask.value in action2.tmp_locations:
                        action2.tmp_locations.remove(var.mask.value)

    def prepare_output(self):
        Action2.prepare_output(self)
        for i in range(0, len(self.var_list) - 1, 2):
            self.var_list[i].shift.value |= 0x20

        for r in self.ranges:
            if isinstance(r.result, basestring):
                 r.result = remove_ref(r.result)
            else:
                 r.result = r.result.value | 0x8000
        if isinstance(self.default_result, basestring):
             self.default_result = remove_ref(self.default_result)
        else:
             self.default_result = self.default_result.value | 0x8000

    def write(self, file):
        global action2operator_to_num
        #type_byte, num_ranges, default_result = 4
        size = 4 + (2 + 2 * self.varsize) * len(self.ranges)
        for var in self.var_list:
            if isinstance(var, basestring):
                size += 1
            else:
                size += var.get_size(self.varsize)

        Action2.write(self, file, size)
        file.print_bytex(self.type_byte)
        file.newline()
        for var in self.var_list:
            if isinstance(var, basestring):
                file.newline()
                file.print_bytex(action2operator_to_num[var], var)
            else:
                var.write(file, self.varsize)
        file.print_byte(len(self.ranges))
        file.newline()
        for r in self.ranges:
            file.print_wordx(r.result)
            file.print_varx(r.min.value, self.varsize)
            file.print_varx(r.max.value, self.varsize)
            file.newline()
        file.print_wordx(self.default_result)
        file.newline()
        file.newline()

def convert_op_to_action2(op):
    op_to_act2 = {
        Operator.ADD: Action2Operator.ADD,
        Operator.SUB: Action2Operator.SUB,
        Operator.DIV: Action2Operator.DIVS,
        Operator.MOD: Action2Operator.MODS,
        Operator.MUL: Action2Operator.MUL,
        Operator.AND: Action2Operator.AND,
        Operator.OR: Action2Operator.OR,
        Operator.XOR: Action2Operator.XOR,
        Operator.MIN: Action2Operator.MIN,
        Operator.MAX: Action2Operator.MAX,
    }
    if not op in op_to_act2: raise ScriptError("Unsupported operator in action2 expression: " + op)
    return op_to_act2[op]

class VarAction2Var:
    def __init__(self, var_num, shift, mask, parameter = None):
        self.var_num = var_num
        self.shift = shift
        self.mask = mask
        self.parameter = parameter
        self.add = None
        self.div = None
        self.mod = None

    def write(self, file, size):
        file.print_bytex(self.var_num)
        if self.parameter is not None: self.parameter.write(file, 1)
        if self.mod is not None:
            self.shift.value |= 0x80
        elif self.add is not None or self.div is not None:
            self.shift.value |= 0x40
        self.shift.write(file, 1)
        self.mask.write(file, size)
        if self.add is not None:
            self.add.write(file, size)
            if self.div is not None:
                self.div.write(file, size)
            elif self.mod is not None:
                self.mod.write(file, size)
            else:
                #no div or add, just divide by 1
                file.print_varx(1, size)

    def get_size(self, varsize):
        #var number [+ parameter] + shift num + and mask
        size = 2 + varsize
        if self.parameter is not None: size += 1
        if self.add is not None or self.div is not None or self.mod is not None: size += varsize * 2
        return size

class VarAction2StoreTempVar(VarAction2Var):
    def __init__(self):
        VarAction2Var.__init__(self, 0x1A, ConstantNumeric(0), ConstantNumeric(0))
        #mask holds the number, it's resolved in Action2Var.resolve_tmp_storage

    def get_size(self, varsize):
        return 2 + varsize

def get_mask(size):
    if size == 1: return 0xFF
    elif size == 2: return 0xFFFF
    return 0xFFFFFFFF

class VarAction2LoadTempVar(VarAction2Var):
    def __init__(self, tmp_var):
        VarAction2Var.__init__(self, 0x7D, ConstantNumeric(0), ConstantNumeric(0))
        assert isinstance(tmp_var, VarAction2StoreTempVar)
        self.tmp_var = tmp_var

    def write(self, file, size):
        self.parameter = self.tmp_var.mask
        self.mask = ConstantNumeric(get_mask(size))
        VarAction2Var.write(self, file, size)

    def get_size(self, varsize):
        return 3 + varsize

class Modification:
    def __init__(self, param, size, offset):
        self.param = param
        self.size = size
        self.offset = offset

def parse_varaction2_expression(expr, varsize):
    extra_actions = []
    mods = []
    var_list = []
    var_list_size = 0

    if isinstance(expr, ConstantNumeric):
        var = VarAction2Var(0x1A, ConstantNumeric(0), expr)
        var_list.append(var)
        var_list_size += var.get_size(varsize)

    elif isinstance(expr, Parameter):
        if isinstance(expr.num, ConstantNumeric):
            param_num = expr.num.value
        else:
            param_num, tmp_param_actions = get_tmp_parameter(expr)
            extra_actions.extend(tmp_param_actions)
        mods.append(Modification(param_num, varsize, var_list_size + 2))
        var = VarAction2Var(0x1A, ConstantNumeric(0), ConstantNumeric(0))
        var_list.append(var)
        var_list_size += var.get_size(varsize)
        target = ConstantNumeric(0)

    elif isinstance(expr, Variable):
        if not isinstance(expr.num, ConstantNumeric):
            raise ScriptError("Variable number must be a constant number")
        if not (expr.param is None or isinstance(expr.param, ConstantNumeric)):
            raise ScriptError("Variable parameter must be a constant number")
        var = VarAction2Var(expr.num.value, expr.shift, expr.mask, expr.param)
        var.add, var.div, var.mod = expr.add, expr.div, expr.mod
        var_list.append(var)
        var_list_size += var.get_size(varsize)

    elif isinstance(expr, BinOp):
        op = convert_op_to_action2(expr.op)

        #parse expression 2 first in case we need to temporary store the result
        if not isinstance(expr.expr2, BinOp):
            expr2 = expr.expr2
        else:
            tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expr.expr2, varsize)
            extra_actions.extend(tmp_actions)
            for mod in tmp_mods:
                mod.offset += var_list_size
            mods.extend(tmp_mods)
            var_list.extend(tmp_var_list)
            tmp_var = VarAction2StoreTempVar()
            var_list.append(Action2Operator.STO_TMP)
            var_list.append(tmp_var)
            var_list.append(Action2Operator.VAL2)
            #the +2 is for both operators
            var_list_size += tmp_var_list_size + 2 + tmp_var.get_size(varsize)
            expr2 = VarAction2LoadTempVar(tmp_var)

        #parse expr1
        tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expr.expr1, varsize)
        extra_actions.extend(tmp_actions)
        for mod in tmp_mods:
            mod.offset += var_list_size
        mods.extend(tmp_mods)
        var_list.extend(tmp_var_list)
        var_list_size += tmp_var_list_size

        var_list.append(op)
        var_list_size += 1

        if isinstance(expr2, VarAction2LoadTempVar):
            var_list.append(expr2)
            var_list_size += expr2.get_size(varsize)
        else:
            tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expr2, varsize)
            #it can be constant, parameter or variable
            assert len(tmp_var_list) == 1
            extra_actions.extend(tmp_actions)
            for mod in tmp_mods:
                mod.offset += var_list_size
            mods.extend(tmp_mods)
            var_list.extend(tmp_var_list)
            var_list_size += tmp_var_list_size

    else:
        raise ScriptError("Invalid expression type in varaction2 expression")

    return (extra_actions, mods, var_list, var_list_size)

def make_return_varact2(switch_block):
    act = Action2Var(switch_block.feature.value, switch_block.name + '@return', 0x89, 4)
    act.var_list = [VarAction2Var(0x1C, ConstantNumeric(0), ConstantNumeric(0xFFFFFFFF))]
    act.default_result = 'CB_FAILED'
    return act

def parse_varaction2(switch_block):
    global free_parameters
    free_parameters_backup = free_parameters[:]
    action6 = Action6()
    return_action = None
    varsize = 4
    feature = switch_block.feature.value if switch_block.var_range == 0x89 else varact2parent_scope[switch_block.feature.value]
    if feature is None: raise ScriptError("Parent scope for this feature not available, feature: " + switch_block.feature)
    varaction2 = Action2Var(switch_block.feature.value, switch_block.name, switch_block.var_range, varsize)

    func = lambda x: Variable(ConstantNumeric(x['var']), ConstantNumeric(x['start']), ConstantNumeric((1 << x['size']) - 1))
    expr = reduce_expr(switch_block.expr, [(varact2vars[feature], func), (varact2_globalvars, func), global_constants.const_table, cargo_numbers])

    offset = 4 #first var

    action_list, mods, var_list, var_list_size = parse_varaction2_expression(expr, varsize)
    for mod in mods:
        action6.modify_bytes(mod.param, mod.size, mod.offset + offset)
    varaction2.var_list = var_list
    offset += var_list_size

    #nvar == 0 is a special case, make sure that isn't triggered here, unless we want it to
    if len(switch_block.body.ranges) == 0 and switch_block.body.default is not None:
        switch_block.body.ranges.append(nml.ast.SwitchRange(ConstantNumeric(0), ConstantNumeric(0), switch_block.body.default))

    for r in switch_block.body.ranges:
        if r.result is None:
            if return_action is None: return_action = make_return_varact2(switch_block)
            action2 = add_ref(return_action.name)
            assert return_action == action2
            varaction2.references.append(action2)
            r.result = return_action.name
        elif isinstance(r.result, basestring):
            if r.result != 'CB_FAILED':
                action2 = add_ref(r.result)
                varaction2.references.append(action2)
        elif not isinstance(r.result, ConstantNumeric):
            raise ScriptError("Result of varaction2 range must be another action2 or a constant number")

        if not isinstance(r.min, ConstantNumeric):
            raise ScriptError("Min value of varaction2 range must be a constant number")
        if not isinstance(r.max, ConstantNumeric):
            raise ScriptError("Max value of varaction2 range must be a constant number")

        varaction2.ranges.append(r)

    default = switch_block.body.default
    if default is None:
        if len(switch_block.body.ranges) == 0:
            #in this case, we can return with nvar == 0 without an extra action2
            default = 'CB_FAILED'
        else:
            if return_action is None: return_action = make_return_varact2(switch_block)
            action2 = add_ref(return_action.name)
            assert action2 == return_action
            varaction2.references.append(action2)
            default = return_action.name
    elif isinstance(default, basestring):
        if default != 'CB_FAILED':
            action2 = add_ref(default)
            varaction2.references.append(action2)
    elif not isinstance(default, ConstantNumeric):
        raise ScriptError("Default result of varaction2 must be another action2 or a constant number")

    varaction2.default_result = default

    if len(action6.modifications) > 0: action_list.append(action6)

    action_list.append(varaction2)
    if return_action is not None: action_list.insert(0, return_action)

    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
