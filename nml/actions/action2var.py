from nml.actions import action2, action6, actionD, action2var_variables, action4
from nml import expression, generic, global_constants, nmlop, unit

class Action2Var(action2.Action2):
    """
    Variational Action2. This is the NFO equivalent of a switch-block in NML.
    It computes a single integer from one or more variables and picks it's
    return value based on the result of the computation. The return value can
    be either a 15bit integer or a reference to another action2.

    @ivar type_byte: The size (byte, word, double word) and access type (own 
                     object or related object). 0x89 (own object, double word)
                     and 0x8A (related object, double word) and the only
                     supported values.
    @type type_byte: C{int}

    @ivar tmp_locations: List of address in the temporary storage that are free
                         to be used in this varaction2.
    @type tmp_locations: C{list} of C{int}

    @ivar ranges: List of return value ranges. Each range contains a minimum and
                  a maximum value and a return value. The list is checked in order,
                  if the result of the computation is between the miminum and
                  maximum (inclusive) of one range the result of that range is
                  returned. The result can be either an integer of another
                  action2.
    @ivar ranges: C{list} of L{SwitchRange}
    """
    def __init__(self, feature, name, type_byte):
        action2.Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        #0x00 - 0x7F: available to user
        #0x80 - 0x85: used for production CB
        #0x86 - 0x100: available as temp. registers
        self.tmp_locations = range(0x86, 0x100)
        self.ranges = []

    def remove_tmp_location(self, location):
        #if we already removed the location from the list of available
        #locations in this Action2Var, we also removed it from all
        #referenced action2's.
        if location not in self.tmp_locations: return
        self.tmp_locations.remove(location)
        #Remove it also from all referenced action2's.
        action2.Action2.remove_tmp_location(self, location)

    def resolve_tmp_storage(self):
        for var in self.var_list:
            if isinstance(var, VarAction2StoreTempVar):
                location = self.tmp_locations[0]
                self.remove_tmp_location(location)
                var.mask = expression.ConstantNumeric(location)

    def prepare_output(self):
        action2.Action2.prepare_output(self)
        for i in range(0, len(self.var_list) - 1, 2):
            self.var_list[i].shift.value |= 0x20

        for r in self.ranges:
            if isinstance(r.result, action2.SpriteGroupRef):
                r.result = action2.remove_ref(r.result.name.value)
            else:
                r.result = r.result.value | 0x8000
        if isinstance(self.default_result, action2.SpriteGroupRef):
            self.default_result = action2.remove_ref(self.default_result.name.value)
        else:
            self.default_result = self.default_result.value | 0x8000

    def write(self, file):
        #type_byte, num_ranges, default_result = 4
        #2 bytes for the result, 8 bytes for the min/max range.
        size = 4 + (2 + 8) * len(self.ranges)
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                size += 1
            else:
                size += var.get_size()

        self.write_sprite_start(file, size)
        file.print_bytex(self.type_byte)
        file.newline()
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                file.newline()
                file.print_bytex(var.act2_num, var.act2_str)
            else:
                var.write(file, 4)
        file.print_byte(len(self.ranges))
        file.newline()
        for r in self.ranges:
            file.print_wordx(r.result)
            file.print_varx(r.min.value, 4)
            file.print_varx(r.max.value, 4)
            file.newline(r.comment)
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

    def get_size(self):
        #var number (1) [+ parameter (1)] + shift num (1) + and mask (4) [+ add (4) + div/mod (4)]
        size = 6
        if self.parameter is not None: size += 1
        if self.add is not None or self.div is not None or self.mod is not None: size += 8
        return size

    def supported_by_actionD(self, raise_error):
        assert not raise_error
        return False

class VarAction2StoreTempVar(VarAction2Var):
    def __init__(self):
        VarAction2Var.__init__(self, 0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(0))
        #mask holds the number, it's resolved in Action2Var.resolve_tmp_storage

    def get_size(self):
        return 6

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

    def get_size(self):
        return 7

class Modification(object):
    def __init__(self, param, size, offset):
        self.param = param
        self.size = size
        self.offset = offset

class SwitchRange(object):
    def __init__(self, min, max, result, unit = None, comment = None):
        self.min = min.reduce(global_constants.const_list)
        self.max = max.reduce(global_constants.const_list)
        if result is None:
            self.result is None
        elif isinstance(result, action2.SpriteGroupRef):
            self.result = result
        else:
            self.result = result.reduce(global_constants.const_list)
        self.unit = unit
        self.comment = comment

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if self.result is None:
            print (indentation+2)*' ' + 'Return computed value'
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if isinstance(self.result, expression.SpriteGroupRef):
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

class Varaction2Parser(object):
    def __init__(self):
        self.extra_actions = []
        self.mods = []
        self.var_list = []
        self.var_list_size = 0


    def preprocess_binop(self, expr):
        """
        Several nml operators are not directly support by nfo so we have to work
        around that by implementing those operators in terms of others.

        @return: A pre-processed version of the expression.
        @rtype:  L{Expression}
        """
        assert isinstance(expr, expression.BinOp)
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
        elif expr.op == nmlop.NOTHASBIT:
            # !hasbit(x, n) ==> ((x >> n) & 1) ^ 1
            expr = expression.BinOp(nmlop.DIV, expr.expr1, pow2(expr.expr2))
            expr = expression.BinOp(nmlop.AND, expr, expression.ConstantNumeric(1))
            expr = expression.BinOp(nmlop.XOR, expr, expression.ConstantNumeric(1))

        return expr


    def preprocess_ternaryop(self, expr):
        assert isinstance(expr, expression.TernaryOp)
        guard = expression.Boolean(expr.guard).reduce()
        self.parse(guard)
        guard_var = VarAction2StoreTempVar()
        inverted_guard_var = VarAction2StoreTempVar()
        self.var_list.append(nmlop.STO_TMP)
        self.var_list.append(guard_var)
        self.var_list.append(nmlop.XOR)
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(1))
        self.var_list.append(var)
        self.var_list.append(nmlop.STO_TMP)
        self.var_list.append(inverted_guard_var)
        self.var_list.append(nmlop.VAL2)
        # the +4 is for the 4 operators added above (STO_TMP, XOR, STO_TMP, VAL2)
        self.var_list_size += 4 + guard_var.get_size() + inverted_guard_var.get_size() + var.get_size()
        expr1 = expression.BinOp(nmlop.MUL, expr.expr1, VarAction2LoadTempVar(guard_var))
        expr2 = expression.BinOp(nmlop.MUL, expr.expr2, VarAction2LoadTempVar(inverted_guard_var))
        return expression.BinOp(nmlop.ADD, expr1, expr2)


    def parse_expr_to_constant(self, expr, offset):
        if isinstance(expr, expression.ConstantNumeric): return expr

        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
        self.extra_actions.extend(tmp_param_actions)
        self.mods.append(Modification(tmp_param, 4, self.var_list_size + offset))
        return expression.ConstantNumeric(0)

    def parse_variable(self, expr):
        if not isinstance(expr.num, expression.ConstantNumeric):
            raise generic.ScriptError("Variable number must be a constant number", expr.num.pos)
        if not (expr.param is None or isinstance(expr.param, expression.ConstantNumeric)):
            raise generic.ScriptError("Variable parameter must be a constant number", expr.param.pos)

        if len(expr.extra_params) > 0:
            first_var = len(self.var_list) == 0
            backup_op = None
            value_backup = None
            if not first_var:
                backup_op = self.var_list.pop()
                value_backup = VarAction2StoreTempVar()
                self.var_list.append(nmlop.STO_TMP)
                self.var_list.append(value_backup)
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += value_backup.get_size() + 1

            #Last value == 0, and this is right before we're going to use
            #the extra parameters. Set them to their correct value here.
            for extra_param in expr.extra_params:
                self.parse(extra_param[1])
                self.var_list.append(nmlop.STO_TMP)
                var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(extra_param[0]))
                self.var_list.append(var)
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += var.get_size() + 2

            if not first_var:
                value_loadback = VarAction2LoadTempVar(value_backup)
                self.var_list.append(value_loadback)
                self.var_list.append(backup_op)
                self.var_list_size += value_loadback.get_size() + 1

        offset = 2 if expr.param is None else 3
        mask = self.parse_expr_to_constant(expr.mask, offset)

        var = VarAction2Var(expr.num.value, expr.shift, mask, expr.param)

        if expr.add is not None:
            var.add = self.parse_expr_to_constant(expr.add, offset + 4)
        if expr.div is not None:
            var.div = self.parse_expr_to_constant(expr.div, offset + 8)
        if expr.mod is not None:
            var.mod = self.parse_expr_to_constant(expr.mod, offset + 8)
        self.var_list.append(var)
        self.var_list_size += var.get_size()


    def parse_binop(self, expr):
        if expr.op.act2_num is None: expr.supported_by_action2(True)

        if isinstance(expr.expr2, (expression.ConstantNumeric, expression.Variable)) or \
                isinstance(expr.expr2, VarAction2LoadTempVar) or \
                (isinstance(expr.expr2, expression.Parameter) and isinstance(expr.expr2.num, expression.ConstantNumeric)) or \
                expr.op == nmlop.VAL2:
            expr2 = expr.expr2
        elif expr.expr2.supported_by_actionD(False):
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr.expr2)
            self.extra_actions.extend(tmp_param_actions)
            expr2 = expression.Parameter(expression.ConstantNumeric(tmp_param))
        else:
            #The expression is so complex we need to compute it first, store the
            #result and load it back later.
            self.parse(expr.expr2)
            tmp_var = VarAction2StoreTempVar()
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(tmp_var)
            self.var_list.append(nmlop.VAL2)
            #the +2 is for both operators
            self.var_list_size += tmp_var.get_size() + 2
            expr2 = VarAction2LoadTempVar(tmp_var)

        #parse expr1
        self.parse(expr.expr1)
        self.var_list.append(expr.op)
        self.var_list_size += 1

        if isinstance(expr2, VarAction2LoadTempVar):
            self.var_list.append(expr2)
            self.var_list_size += expr2.get_size()
        else:
            self.parse(expr2)


    def parse_constant(self, expr):
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expr)
        self.var_list.append(var)
        self.var_list_size += var.get_size()


    def parse_param(self, expr):
        self.mods.append(Modification(expr.num.value, 4, self.var_list_size + 2))
        var = VarAction2Var(0x1A, expression.ConstantNumeric(0), expression.ConstantNumeric(0))
        self.var_list.append(var)
        self.var_list_size += var.get_size()


    def parse_string(self, expr):
        str_id, size_2, actions = action4.get_string_action4s(0, 0xD0, expr)
        self.extra_actions.extend(actions)
        self.parse_constant(expression.ConstantNumeric(str_id))


    def parse_via_actionD(self, expr):
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
        self.extra_actions.extend(tmp_param_actions)
        num = expression.ConstantNumeric(tmp_param)
        self.parse(expression.Parameter(num))


    def parse(self, expr):
        #Preprocess the expression
        if isinstance(expr, expression.SpecialParameter):
            #do this first, since it may evaluate to a BinOp
            expr = expr.to_reading()

        if isinstance(expr, expression.BinOp):
            expr = self.preprocess_binop(expr)

        elif isinstance(expr, expression.Boolean):
            expr = expression.BinOp(nmlop.MINU, expr.expr, expression.ConstantNumeric(1))

        elif isinstance(expr, expression.Not):
            expr = expression.BinOp(nmlop.XOR, expr.expr, expression.ConstantNumeric(1))

        elif isinstance(expr, expression.BinNot):
            expr = expression.BinOp(nmlop.XOR, expr.expr, expression.ConstantNumeric(0xFFFFFFFF))

        elif isinstance(expr, expression.TernaryOp) and not expr.supported_by_actionD(False):
            expr = self.preprocess_ternaryop(expr)

        #Try to parse the expression to a list of variables+operators
        if isinstance(expr, expression.ConstantNumeric):
            self.parse_constant(expr)

        elif isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
            self.parse_param(expr)

        elif isinstance(expr, expression.Variable):
            self.parse_variable(expr)

        elif expr.supported_by_actionD(False):
            self.parse_via_actionD(expr)

        elif isinstance(expr, expression.BinOp):
            self.parse_binop(expr)

        elif isinstance(expr, expression.String):
            self.parse_string(expr)

        else:
            expr.supported_by_action2(True)
            assert False #supported_by_action2 should have raised the correct error already

def make_return_ref(str, pos):
    return action2.SpriteGroupRef(expression.Identifier(str, pos), [], pos)

def make_return_varact2(switch_block):
    act = Action2Var(switch_block.feature.value, switch_block.name.value + '@return', 0x89)
    act.var_list = [VarAction2Var(0x1C, expression.ConstantNumeric(0), expression.ConstantNumeric(0xFFFFFFFF))]
    act.default_result = make_return_ref('CB_FAILED', switch_block.pos)
    return act

def parse_var(info, pos):
    res = expression.Variable(expression.ConstantNumeric(info['var']), expression.ConstantNumeric(info['start']), expression.ConstantNumeric((1 << info['size']) - 1), None, pos)
    if 'function' in info:
        return info['function'](res, info)
    return res

def parse_60x_var(name, args, pos, info):
    if 'function' in info:
        return info['function'](name, args, pos, info)
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

def parse_minmax(value, unit, action_list, act6, offset):
    """
    Parse a min or max value in a switch block.

    @param value: Value to parse
    @type value: L{Expression}

    @param unit: Unit to use
    @type unit: C{str} or C{None}

    @param action_list: List to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param act6: Action6 to add any modifications to
    @type act6: L{Action6}

    @param offset: Current offset to use for action6
    @type offset: C{int}

    @return: A tuple of two values:
                - The value to use as min/max
                - Whether the resulting range may need a sanity check
    @rtype: C{tuple} of (L{ConstantNumeric} or L{SpriteGroupRef}), C{bool}
    """
    check_range = True
    if unit is not None:
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Using a unit is only allowed in combination with a compile-time constant", value.pos)
        assert unit in unit.units
        result = expression.ConstantNumeric(int(value.value / unit.units[unit]['convert']))
    elif isinstance(value, expression.ConstantNumeric):
        result = value
    elif isinstance(value, expression.Parameter) and isinstance(value.num, expression.ConstantNumeric):
        act6.modify_bytes(value.num.value, 4, offset)
        result = expression.ConstantNumeric(0)
        check_range = False
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(value)
        action_list.extend(tmp_param_actions)
        act6.modify_bytes(tmp_param, 4, offset)
        result = expression.ConstantNumeric(0)
        check_range = False
    return (result, check_range)

def parse_result(value, action_list, act6, offset, varaction2, return_action, need_return_action = True):
    """
    Parse a result (another switch or CB result) in a switch block.

    @param value: Value to parse
    @type value: L{Expression}, L{None} or L{SpriteGroupRef}

    @param action_list: List to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param act6: Action6 to add any modifications to
    @type act6: L{Action6}

    @param offset: Current offset to use for action6
    @type offset: C{int}

    @param varaction2: Reference to the resulting varaction2
    @type varaction2: L{Action2Var}

    @param return_action: Reference to the action2 used to return the computed value, if defined.
    @type return_action: L{Action2Var} or C{None}

    @param switch_block: Reference to the switch block that is being compiled
    @type switch_block: L{Switch}

    @return: A tuple of three values:
                - The value to use as return value
                - Comment to add to this value
                - New value of C{return_action} (see the parameter)
    @rtype: C{tuple} of (L{ConstantNumeric} or L{SpriteGroupRef}), C{str}, (L{Action2Var} or C{None})
    """
    if value is None:
        comment = "return;"
        if len(switch_block.body.ranges) != 0:
            if return_action is None: return_action = make_return_varact2(switch_block)
            act2 = action2.add_ref(return_action.name, switch_block.pos)
            assert return_action == act2
            varaction2.references.add(act2)
            result = make_return_ref(return_action.name, switch_block.pos)
        else:
            default = make_return_ref('CB_FAILED', switch_block.pos)
    elif isinstance(value, action2.SpriteGroupRef):
        comment = value.name.value + ';'
        if value.name.value != 'CB_FAILED':
            act2 = action2.add_ref(value.name.value, value.pos)
            varaction2.references.add(act2)
        result = value
    elif isinstance(value, expression.ConstantNumeric):
        comment = "return %d;" % value.value
        result = value
    elif isinstance(value, expression.Parameter) and isinstance(value.num, expression.ConstantNumeric):
        comment = "return %s;" % str(value)
        act6.modify_bytes(value.num.value, 4, offset)
        result = expression.ConstantNumeric(0)
    elif isinstance(value, expression.String):
        comment = "return %s;" % str(value)
        str_id, size_2, actions = action4.get_string_action4s(0, 0xD0, value)
        action_list.extend(actions)
        result = expression.ConstantNumeric(str_id - 0xD000 + 0x8000)
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(value)
        comment = "return param[%d];" % tmp_param
        action_list.extend(tmp_param_actions)
        act6.modify_bytes(tmp_param, 2, offset)
        result = expression.ConstantNumeric(0)
    return (result, comment, return_action)

def parse_varaction2(switch_block):
    action6.free_parameters.save()
    act6 = action6.Action6()
    return_action = None
    feature = switch_block.feature.value if switch_block.var_range == 0x89 else action2var_variables.varact2parent_scope[switch_block.feature.value]
    if feature is None: raise generic.ScriptError("Parent scope for this feature not available, feature: " + str(switch_block.feature), switch_block.pos)
    varaction2 = Action2Var(switch_block.feature.value, switch_block.name.value, switch_block.var_range)

    func60x = lambda name, value: expression.FunctionPtr(name, parse_60x_var, value)
    #make sure, that variables take precedence about global constants / parameters
    #this way, use the current climate instead of the climate at load time.
    expr = switch_block.expr.reduce([(action2var_variables.varact2_globalvars, parse_var), \
        (action2var_variables.varact2vars[feature], parse_var), \
        (action2var_variables.varact2vars60x[feature], func60x)] + \
        global_constants.const_list)

    offset = 4 #first var

    parser = Varaction2Parser()
    parser.parse(expr)
    action_list = parser.extra_actions
    for mod in parser.mods:
        act6.modify_bytes(mod.param, mod.size, mod.offset + offset)
    varaction2.var_list = parser.var_list
    offset += parser.var_list_size + 1 # +1 for the byte num-ranges

    #nvar == 0 is a special case, make sure that isn't triggered here, unless we want it to
    if len(switch_block.body.ranges) == 0 and switch_block.body.default is not None:
        switch_block.body.ranges.append(SwitchRange(expression.ConstantNumeric(0), expression.ConstantNumeric(0), switch_block.body.default))

    used_ranges = []
    for r in switch_block.body.ranges:
        comment = str(r.min) + " .. " + str(r.max) + ": "

        range_result, range_comment, return_action = parse_result(r.result, action_list, act6, offset, varaction2, return_action, switch_block)
        comment += range_comment
        offset += 2 # size of result

        range_min, check_min = parse_minmax(r.min, r.unit, action_list, act6, offset)
        offset += 4
        range_max, check_max = parse_minmax(r.max, r.unit, action_list, act6, offset)
        offset += 4

        range_overlap = False
        if check_min and check_max:
            for existing_range in used_ranges:
                if existing_range[0] <= range_min.value and range_max.value <= existing_range[1]:
                    generic.print_warning("Range overlaps with existing ranges so it'll never be reached", r.min.pos)
                    range_overlap = True
                    break
            if not range_overlap:
                used_ranges.append([range_min.value, range_max.value])
                used_ranges.sort()
                i = 0
                while i + 1 < len(used_ranges):
                    if used_ranges[i + 1][0] <= used_ranges[i][1] + 1:
                        used_ranges[i][1] = max(used_ranges[i][1], used_ranges[i + 1][1])
                        used_ranges.pop(i + 1)
                    else:
                        i += 1

        if not range_overlap:
            varaction2.ranges.append(SwitchRange(range_min, range_max, range_result, comment=comment))

    default, default_comment, return_action = parse_result(switch_block.body.default, action_list, act6, offset, varaction2, return_action, switch_block)
    varaction2.default_result = default

    if len(act6.modifications) > 0: action_list.append(act6)

    action_list.append(varaction2)
    if return_action is not None: action_list.insert(0, return_action)

    action6.free_parameters.restore()
    return action_list
