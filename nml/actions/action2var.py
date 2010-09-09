from nml.actions import action2, action6, actionD, action2var_variables, action4
from nml import expression, generic, global_constants, nmlop

class Action2Operator(object):
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
    STO_PERM = r'10'

class Action2Var(action2.Action2):
    def __init__(self, feature, name, type_byte, varsize):
        action2.Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        self.varsize = varsize
        #0x00 - 0x7F: available to user
        #0x80 - 0x85: used for production CB
        #0x86 - 0x100: available as temp. registers
        self.tmp_locations = range(0x86, 0x100)
        self.references = []
        self.ranges = []

    def resolve_tmp_storage(self):
        self.references = set(self.references)
        for var in self.var_list:
            if isinstance(var, VarAction2StoreTempVar):
                var.mask = expression.ConstantNumeric(self.tmp_locations.pop())
                for act2 in self.references:
                    if isinstance(act2, Action2Var) and var.mask.value in act2.tmp_locations:
                        act2.tmp_locations.remove(var.mask.value)

    def prepare_output(self):
        action2.Action2.prepare_output(self)
        for i in range(0, len(self.var_list) - 1, 2):
            self.var_list[i].shift.value |= 0x20

        for r in self.ranges:
            if isinstance(r.result, expression.Identifier):
                r.result = action2.remove_ref(r.result.value)
            else:
                r.result = r.result.value | 0x8000
        if isinstance(self.default_result, expression.Identifier):
            self.default_result = action2.remove_ref(self.default_result.value)
        else:
            self.default_result = self.default_result.value | 0x8000

    def write(self, file):
        #type_byte, num_ranges, default_result = 4
        size = 4 + (2 + 2 * self.varsize) * len(self.ranges)
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                size += 1
            else:
                size += var.get_size(self.varsize)

        self.write_sprite_start(file, size)
        file.print_bytex(self.type_byte)
        file.newline()
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                file.newline()
                file.print_bytex(var.act2_num, var.act2_str)
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
        file.end_sprite()

class VarAction2Var(object):
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

    def supported_by_actionD(self, raise_error):
        assert not raise_error
        return False

class VarAction2StoreTempVar(VarAction2Var):
    def __init__(self):
        VarAction2Var.__init__(self, 0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(0))
        #mask holds the number, it's resolved in Action2Var.resolve_tmp_storage

    def get_size(self, varsize):
        return 2 + varsize

def get_mask(size):
    if size == 1: return 0xFF
    elif size == 2: return 0xFFFF
    return 0xFFFFFFFF

class VarAction2LoadTempVar(VarAction2Var):
    def __init__(self, tmp_var):
        VarAction2Var.__init__(self, 0x7D, expression.ConstantNumeric(0), expression.ConstantNumeric(0))
        assert isinstance(tmp_var, VarAction2StoreTempVar)
        self.tmp_var = tmp_var

    def write(self, file, size):
        self.parameter = self.tmp_var.mask
        self.mask = expression.ConstantNumeric(get_mask(size))
        VarAction2Var.write(self, file, size)

    def get_size(self, varsize):
        return 3 + varsize

class Modification(object):
    def __init__(self, param, size, offset):
        self.param = param
        self.size = size
        self.offset = offset

class SwitchRange(object):
    def __init__(self, min, max, result):
        self.min = min.reduce(global_constants.const_list)
        self.max = max.reduce(global_constants.const_list)
        self.result = result.reduce(global_constants.const_list, False) if result is not None else None

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.result.debug_print(indentation + 4)
        elif self.result is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if isinstance(self.result, expression.Identifier):
            ret += ': %s;' % str(self.result)
        elif self.result is None:
            ret += ': return;'
        else:
            ret += ': return %s;' % str(self.result)
        return ret

def pow2(expr):
    #2**x = (1 ror (32 - x))
    if isinstance(expr, expression.ConstantNumeric):
        return expression.ConstantNumeric(1 << expr.value)
    expr = expression.BinOp(nmlop.SUB, expression.ConstantNumeric(32), expr)
    expr = expression.BinOp(nmlop.ROT_RIGHT, expression.ConstantNumeric(1), expr)
    return expr

def parse_varaction2_expression(expr, varsize):
    extra_actions = []
    mods = []
    var_list = []
    var_list_size = 0

    if isinstance(expr, expression.BinOp):
        if expr.op == nmlop.CMP_LT:
            #return value is 0, 1 or 2, we want to map 0 to 1 and the others to 0
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            #reduce the problem to 0/1
            expr = expression.BinOp(nmlop.MIN, expr, expression.ConstantNumeric(1))
            #and invert the result
            expr = expression.BinOp(nmlop.XOR, expr, expression.ConstantNumeric(1))
        elif expr.op == nmlop.CMP_GT:
            #return value is 0, 1 or 2, we want to map 2 to 1 and the others to 0
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            #subtract one
            expr = expression.BinOp(nmlop.SUB, expr, expression.ConstantNumeric(1))
            #map -1 and 0 to 0
            expr = expression.BinOp(nmlop.MAX, expr, expression.ConstantNumeric(0))
        elif expr.op == nmlop.CMP_LE:
            #return value is 0, 1 or 2, we want to map 2 to 0 and the others to 1
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            #swap 0 and 2
            expr = expression.BinOp(nmlop.XOR, expr, expression.ConstantNumeric(2))
            #map 1/2 to 1
            expr = expression.BinOp(nmlop.MIN, expr, expression.ConstantNumeric(1))
        elif expr.op == nmlop.CMP_GE:
            #return value is 0, 1 or 2, we want to map 1/2 to 1
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            expr = expression.BinOp(nmlop.MIN, expr, expression.ConstantNumeric(1))
        elif expr.op == nmlop.CMP_EQ:
            #return value is 0, 1 or 2, we want to map 1 to 1, other to 0
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric(1))
        elif expr.op == nmlop.CMP_NEQ:
            #same as CMP_EQ but invert the result
            expr = expression.BinOp(nmlop.VACT2_CMP, expr.expr1, expr.expr2)
            expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric(1))
            expr = expression.BinOp(nmlop.XOR, expr, expression.ConstantNumeric(1))

        elif expr.op == nmlop.SHIFT_LEFT:
            #a << b ==> a * (2**b)
            expr = expression.BinOp(nmlop.MUL, expr.expr1, pow2(expr.expr2))
        elif expr.op == nmlop.SHIFT_RIGHT:
            #a >> b ==> a / (2**b)
            expr = expression.BinOp(nmlop.DIV, expr.expr1, pow2(expr.expr2))
        elif expr.op == nmlop.SHIFTU_RIGHT:
            #a >>> b ==> (uint)a / (2**b)
            expr = expression.BinOp(nmlop.DIVU, expr.expr1, pow2(expr.expr2))
        elif expr.op == nmlop.HASBIT:
            # hasbit(x, n) ==> (x >> n) & 1
            expr = expression.BinOp(nmlop.DIV, expr.expr1, pow2(expr.expr2))
            expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric(1))

    elif isinstance(expr, expression.Boolean):
        expr = expression.BinOp(nmlop.MINU, expr.expr, expression.ConstantNumeric(1))

    elif isinstance(expr, expression.Not):
        expr = expression.BinOp(nmlop.XOR, expr.expr, expression.ConstantNumeric(1))

    elif isinstance(expr, expression.BinNot):
        expr = expression.BinOp(nmlop.XOR, expr.expr, expression.ConstantNumeric(0xFFFFFFFF))

    elif isinstance(expr, expression.TernaryOp):
        guard = expression.Boolean(expr.guard).reduce()
        actions, mods, var_list, var_list_size = parse_varaction2_expression(guard, varsize)
        guard_var = VarAction2StoreTempVar()
        inverted_guard_var = VarAction2StoreTempVar()
        var_list.append(nmlop.STO_TMP)
        var_list.append(guard_var)
        var_list.append(nmlop.XOR)
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(1))
        var_list.append(var)
        var_list.append(nmlop.STO_TMP)
        var_list.append(inverted_guard_var)
        var_list.append(nmlop.VAL2)
        # the +4 is for the 4 operators added above (STO_TMP, XOR, STO_TMP, VAL2)
        var_list_size += 4 + guard_var.get_size(varsize) + inverted_guard_var.get_size(varsize) + var.get_size(varsize)
        expr1 = expression.BinOp(nmlop.MUL, expr.expr1, VarAction2LoadTempVar(guard_var))
        expr2 = expression.BinOp(nmlop.MUL, expr.expr2, VarAction2LoadTempVar(inverted_guard_var))
        expr = expression.BinOp(nmlop.ADD, expr1, expr2)

    if isinstance(expr, expression.ConstantNumeric):
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expr)
        var_list.append(var)
        var_list_size += var.get_size(varsize)

    elif isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
        mods.append(Modification(expr.num.value, varsize, var_list_size + 2))
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(0))
        var_list.append(var)
        var_list_size += var.get_size(varsize)
        target = expression.ConstantNumeric(0)

    elif isinstance(expr, expression.Variable):
        if not isinstance(expr.num, expression.ConstantNumeric):
            raise generic.ScriptError("Variable number must be a constant number", expr.num.pos)
        if not (expr.param is None or isinstance(expr.param, expression.ConstantNumeric)):
            raise generic.ScriptError("Variable parameter must be a constant number", expr.param.pos)
        var = VarAction2Var(expr.num.value, expr.shift, expr.mask, expr.param)
        var.add, var.div, var.mod = expr.add, expr.div, expr.mod
        var_list.append(var)
        var_list_size += var.get_size(varsize)

    elif expr.supported_by_actionD(False):
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
        extra_actions.extend(tmp_param_actions)
        num = expression.ConstantNumeric(tmp_param)
        tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expression.Parameter(num), varsize)
        extra_actions.extend(tmp_actions)
        for mod in tmp_mods:
            mod.offset += var_list_size
        mods.extend(tmp_mods)
        var_list.extend(tmp_var_list)
        var_list_size += tmp_var_list_size

    elif isinstance(expr, expression.BinOp):
        if expr.op.act2_num is None: expr.supported_by_action2(True)

        if isinstance(expr.expr2, (expression.ConstantNumeric, expression.Variable)) or \
                isinstance(expr.expr2, VarAction2LoadTempVar) or \
                (isinstance(expr.expr2, expression.Parameter) and isinstance(expr.expr2.num, expression.ConstantNumeric)) or \
                expr.op == nmlop.VAL2:
            expr2 = expr.expr2
        elif expr.expr2.supported_by_actionD(False):
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr.expr2)
            extra_actions.extend(tmp_param_actions)
            expr2 = expression.Parameter(expression.ConstantNumeric(tmp_param))
        else:
            #The expression is so complex we need to compute it first, store the
            #result and load it back later.
            tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expr.expr2, varsize)
            extra_actions.extend(tmp_actions)
            for mod in tmp_mods:
                mod.offset += var_list_size
            mods.extend(tmp_mods)
            var_list.extend(tmp_var_list)
            tmp_var = VarAction2StoreTempVar()
            var_list.append(nmlop.STO_TMP)
            var_list.append(tmp_var)
            var_list.append(nmlop.VAL2)
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

        var_list.append(expr.op)
        var_list_size += 1

        if isinstance(expr2, VarAction2LoadTempVar):
            var_list.append(expr2)
            var_list_size += expr2.get_size(varsize)
        else:
            tmp_actions, tmp_mods, tmp_var_list, tmp_var_list_size = parse_varaction2_expression(expr2, varsize)
            #it can be constant, parameter or variable
            assert len(tmp_var_list) == 1 or expr.op == nmlop.VAL2
            extra_actions.extend(tmp_actions)
            for mod in tmp_mods:
                mod.offset += var_list_size
            mods.extend(tmp_mods)
            var_list.extend(tmp_var_list)
            var_list_size += tmp_var_list_size

    else:
        expr.supported_by_action2(True)
        assert False #supported_by_action2 should have raised the correct error already

    return (extra_actions, mods, var_list, var_list_size)

def make_return_varact2(switch_block):
    act = Action2Var(switch_block.feature.value, switch_block.name.value + '@return', 0x89, 4)
    act.var_list = [VarAction2Var(0x1C, expression.ConstantNumeric(0), expression.ConstantNumeric(0xFFFFFFFF))]
    act.default_result = expression.Identifier('CB_FAILED', switch_block.pos)
    return act

def parse_60x_var(name, args, pos, info):
    if 'tile' in info:
        narg = 2
        if info['tile'] == 's': minmax = (-8, 7)
        elif info['tile'] == 'u': minmax = (0, 15)
        else: assert False
    else:
        narg = 1
        minmax = (0, 255)

    if len(args) != narg:
        raise generic.ScriptError("'%s'() requires %d argument(s), encountered %d" % (name, narg, len(args)), pos)
    for arg in args:
        if not isinstance(arg, expression.ConstantNumeric):
            raise generic.ScriptError("Arguments of '%s' must be compile-time constants." % name, arg.pos)
        generic.check_range(arg.value, minmax[0], minmax[1], "Argument of '%s'" % name, arg.pos)

    if 'tile' in info:
        param = expression.ConstantNumeric(args[0].value & 0xF)
        param.value |= (args[1].value & 0xF) << 4
    else:
        param = args[0]
    return expression.Variable(expression.ConstantNumeric(info['var']), expression.ConstantNumeric(info['start']), expression.ConstantNumeric((1 << info['size']) - 1), param, pos)

def parse_varaction2(switch_block):
    action6.free_parameters.save()
    act6 = action6.Action6()
    return_action = None
    varsize = 4
    feature = switch_block.feature.value if switch_block.var_range == 0x89 else action2var_variables.varact2parent_scope[switch_block.feature.value]
    if feature is None: raise generic.ScriptError("Parent scope for this feature not available, feature: " + str(switch_block.feature), switch_block.pos)
    varaction2 = Action2Var(switch_block.feature.value, switch_block.name.value, switch_block.var_range, varsize)

    func = lambda x, pos: expression.Variable(expression.ConstantNumeric(x['var']), expression.ConstantNumeric(x['start']), expression.ConstantNumeric((1 << x['size']) - 1), None, pos)
    func60x = lambda name, value: expression.FunctionPtr(name, parse_60x_var, value)
    expr = switch_block.expr.reduce(global_constants.const_list + \
        [(action2var_variables.varact2vars[feature], func), \
        (action2var_variables.varact2_globalvars, func), \
        (action2var_variables.varact2vars60x_test, func60x)])

    offset = 4 #first var

    action_list, mods, var_list, var_list_size = parse_varaction2_expression(expr, varsize)
    for mod in mods:
        act6.modify_bytes(mod.param, mod.size, mod.offset + offset)
    varaction2.var_list = var_list
    offset += var_list_size + 1 # +1 for the byte num-ranges

    #nvar == 0 is a special case, make sure that isn't triggered here, unless we want it to
    if len(switch_block.body.ranges) == 0 and switch_block.body.default is not None:
        switch_block.body.ranges.append(SwitchRange(expression.ConstantNumeric(0), expression.ConstantNumeric(0), switch_block.body.default))

    for r in switch_block.body.ranges:
        if r.result is None:
            if return_action is None: return_action = make_return_varact2(switch_block)
            act2 = action2.add_ref(return_action.name)
            assert return_action == act2
            varaction2.references.append(act2)
            range_result = expression.Identifier(return_action.name, switch_block.pos)
        elif isinstance(r.result, expression.Identifier):
            if r.result.value != 'CB_FAILED':
                act2 = action2.add_ref(r.result.value)
                varaction2.references.append(act2)
            range_result = r.result
        elif isinstance(r.result, expression.ConstantNumeric):
            range_result = r.result
        elif isinstance(r.result, expression.Parameter) and isinstance(r.result.num, expression.ConstantNumeric):
            act6.modify_bytes(r.result.num.value, varsize, offset)
            range_result = expression.ConstantNumeric(0)
        elif isinstance(r.result, expression.String):
            str_id, size_2, actions = action4.get_string_action4s(0, 0xD0, r.result)
            action_list.extend(actions)
            range_result = expression.ConstantNumeric(str_id - 0xD000 + 0x8000)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(r.result)
            action_list.extend(tmp_param_actions)
            act6.modify_bytes(tmp_param, 2, offset)
            range_result = expression.ConstantNumeric(0)

        offset += 2 # size of result

        if isinstance(r.min, expression.ConstantNumeric):
            range_min = r.min
        elif isinstance(r.min, expression.Parameter) and isinstance(r.min.num, expression.ConstantNumeric):
            act6.modify_bytes(r.min.num.value, varsize, offset)
            range_min = expression.ConstantNumeric(0)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(r.min)
            action_list.extend(tmp_param_actions)
            act6.modify_bytes(tmp_param, varsize, offset)
            range_min = expression.ConstantNumeric(0)
        offset += varsize

        if isinstance(r.max, expression.ConstantNumeric):
            range_max = r.max
        elif isinstance(r.max, expression.Parameter) and isinstance(r.max.num, expression.ConstantNumeric):
            act6.modify_bytes(r.max.num.value, varsize, offset)
            range_max = expression.ConstantNumeric(0)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(r.max)
            action_list.extend(tmp_param_actions)
            act6.modify_bytes(tmp_param, varsize, offset)
            range_max = expression.ConstantNumeric(0)
        offset += varsize

        varaction2.ranges.append(SwitchRange(range_min, range_max, range_result))

    default = switch_block.body.default

    if default is None:
        if len(switch_block.body.ranges) == 0:
            #in this case, we can return with nvar == 0 without an extra action2
            default = expression.Identifier('CB_FAILED', switch_block.pos)
        else:
            if return_action is None: return_action = make_return_varact2(switch_block)
            act2 = action2.add_ref(return_action.name)
            assert act2 == return_action
            varaction2.references.append(act2)
            default = expression.Identifier(return_action.name, switch_block.pos)
    elif isinstance(default, expression.Identifier):
        if default.value != 'CB_FAILED':
            act2 = action2.add_ref(default.value)
            varaction2.references.append(act2)
    elif isinstance(default, expression.ConstantNumeric):
        pass
    elif isinstance(default, expression.Parameter) and isinstance(default.num, expression.ConstantNumeric):
        act6.modify_bytes(default.num.value, varsize, offset)
        default = expression.ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(default)
        action_list.extend(tmp_param_actions)
        act6.modify_bytes(tmp_param, 2, offset)
        default = expression.ConstantNumeric(0)

    varaction2.default_result = default

    if len(act6.modifications) > 0: action_list.append(act6)

    action_list.append(varaction2)
    if return_action is not None: action_list.insert(0, return_action)

    action6.free_parameters.restore()
    return action_list
