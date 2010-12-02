import datetime, calendar
from nml import generic, nmlop, grfstrings

class Type(object):
    """
    Enum-type class of the various value types possible in NML
    """
    INTEGER = 0
    FLOAT = 1
    STRING_LITERAL = 2
    FUNCTION_PTR = 3

class Expression(object):
    """
    Superclass for all expression classes.

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """
    def __init__(self, pos):
        self.pos = pos

    def debug_print(self, indentation):
        """
        Print all data with explanation of what it is to standard output.

        @param indentation: Indent all printed lines with at least
            C{indentation} spaces.
        """
        raise NotImplementedError('debug_print must be implemented in expression-subclass %r' % type(self))

    def __str__(self):
        """
        Convert this expression to a string representing this expression in valid NML-code.

        @return: A string representation of this expression.
        """
        raise NotImplementedError('__str__ must be implemented in expression-subclass %r' % type(self))

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        """
        Reduce this expression to the simplest representation possible.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.
        @param unknown_id_fatal: Is encountering an unknown identifier somewhere
            in this expression a fatal error?

        @return: A deep copy of this expression simplified as much as possible.
        """
        raise NotImplementedError('reduce must be implemented in expression-subclass %r' % type(self))

    def reduce_constant(self, id_dicts = []):
        """
        Reduce this expression and make sure the result is a constant number.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.

        @return: A constant number that is the result of this expression.
        """
        expr = self.reduce(id_dicts)
        if not isinstance(expr, (ConstantNumeric, ConstantFloat)):
            raise generic.ConstError(self.pos)
        return expr

    def supported_by_action2(self, raise_error):
        """
        Check if this expression can be used inside a switch-block.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by advanced varaction2.
        """
        if raise_error: raise generic.ScriptError("This expression is not supported in a switch-block", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        """
        Check if this expression can be used inside a parameter-assignment.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by actionD.
        """
        if raise_error: raise generic.ScriptError("This expression can not be assigned to a parameter", self.pos)
        return False

    def is_boolean(self):
        """
        Check if this expression is limited to 0 or 1 as value.

        @return: True if the value of this expression is either 0 or 1.
        """
        return False
    
    def type(self):
        """
        Determine the datatype of this expression.

        @return: A constant from the L{Type} class, representing the data type.
        """
        return Type.INTEGER

class ConstantNumeric(Expression):
    def __init__(self, value, pos = None):
        Expression.__init__(self, pos)
        self.value = generic.truncate_int32(value)

    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value

    def write(self, file, size):
        file.print_varx(self.value, size)

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        return True

    def is_boolean(self):
        return self.value == 0 or self.value == 1

class ConstantFloat(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Float:', self.value

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self
    
    def type(self):
        return Type.FLOAT

class BitMask(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        ret = ConstantNumeric(0, self.pos)
        for orig_expr in self.values:
            val = orig_expr.reduce(id_dicts)
            if val.type() != Type.INTEGER:
                raise generic.ScriptError("Parameters of 'bitmask' must be integers.", orig_expr.pos)
            if isinstance(val, ConstantNumeric) and val.value >= 32:
                raise generic.ScriptError("Parameters of 'bitmask' cannot be greater then 31", orig_expr.pos)
            val = BinOp(nmlop.SHIFT_LEFT, ConstantNumeric(1), val, val.pos)
            ret = BinOp(nmlop.OR, ret, val, self.pos)
        return ret.reduce()

    def __str__(self):
        return "bitmask(" + ", ".join(str(e) for e in self.values) + ")"

class BinOp(Expression):
    def __init__(self, op, expr1, expr2, pos = None):
        Expression.__init__(self, pos)
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op.token
        self.expr1.debug_print(indentation + 2)
        self.expr2.debug_print(indentation + 2)

    def __str__(self):
        return self.op.to_string(self.expr1, self.expr2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(expr1, ConstantNumeric) and isinstance(expr2, ConstantNumeric) and self.op.compiletime_func:
            return ConstantNumeric(self.op.compiletime_func(expr1.value, expr2.value), self.pos)
        if isinstance(expr1, StringLiteral) and isinstance(expr2, StringLiteral):
            if self.op == nmlop.ADD:
                return StringLiteral(expr1.value + expr2.value, expr1.pos)
            raise generic.ScriptError("Only the '+'-operator is supported for literal strings.", self.pos)
        if expr1.type() != Type.INTEGER or expr2.type() != Type.INTEGER:
            raise generic.ScriptError("Both operands of a binary operator must be integers.", self.pos)
        # From lowest to highest prio:
        # -1: everything else (most notable complex expressions like BinOp)
        #  0: Variable
        #  1: something supported by actionD/action7 (but not a constant numeric)
        #  2: ConstantNumeric
        # If the operator allows it we swap the two expressions so that the one with the lower priority
        # is on the left. This makes it possible to do some simple assumptions on that later on.
        if isinstance(expr1, Variable): prio1 = 0
        elif isinstance(expr1, ConstantNumeric): prio1 = 2
        elif expr1.supported_by_actionD(False): prio1 = 1
        else: prio1 = -1
        if isinstance(expr2, Variable): prio2 = 0
        elif isinstance(expr2, ConstantNumeric): prio2 = 2
        elif expr2.supported_by_actionD(False): prio2 = 1
        else: prio2 = -1
        op = self.op
        if prio2 < prio1:
            if op in commutative_operators or self.op in (nmlop.CMP_LT, nmlop.CMP_GT):
                expr1, expr2 = expr2, expr1
                if op == nmlop.CMP_LT:
                    op = nmlop.CMP_GT
                elif op == nmlop.CMP_GT:
                    op = nmlop.CMP_LT
        if op == nmlop.AND and isinstance(expr2, ConstantNumeric) and (expr2.value == -1 or expr2.value == 0xFFFFFFFF):
            return expr1
        if isinstance(expr1, Variable) and expr2.supported_by_actionD(False):
            # An action2 Variable has some special fields (mask, add, div and mod) that can be used
            # to perform some operations on the value. These operations are faster than a normal
            # advanced varaction2 operator so we try to use them whenever we can.
            if op == nmlop.AND and expr1.add is None:
                expr1.mask = BinOp(nmlop.AND, expr1.mask, expr2, self.pos).reduce(id_dicts)
                return expr1
            if op == nmlop.ADD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = expr2
                else: expr1.add = BinOp(nmlop.ADD, expr1.add, expr2, self.pos).reduce(id_dicts)
                return expr1
            if op == nmlop.SUB and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.add = BinOp(nmlop.SUB, expr1.add, expr2, self.pos).reduce(id_dicts)
                return expr1
            # The div and mod fields cannot be used at the same time. Also whenever either of those
            # two are used the add field has to be set, so we change it to zero when it's not yet set.
            if op == nmlop.DIV and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.div = expr2
                return expr1
            if op == nmlop.MOD and expr1.div is None and expr1.mod is None:
                if expr1.add is None: expr1.add = ConstantNumeric(0)
                expr1.mod = expr2
                return expr1
        return BinOp(op, expr1, expr2, self.pos)

    def supported_by_action2(self, raise_error):
        if not self.op.act2_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error: raise generic.ScriptError("Operator%s not supported in a switch-block" % token, self.pos)
            return False
        return self.expr1.supported_by_action2(raise_error) and self.expr2.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        if not self.op.actd_supports:
            token = " '%s'" % self.op.token if self.op.token else ""
            if raise_error:
                if self.op == nmlop.STO_PERM: raise generic.ScriptError("STORE_PERM is only available in switch-blocks.", self.pos)
                elif self.op == nmlop.STO_TMP: raise generic.ScriptError("STORE_TEMP is only available in switch-blocks.", self.pos)
                #default case
                raise generic.ScriptError("Operator%s not supported in parameter assignment" % token, self.pos)
            return False
        return self.expr1.supported_by_actionD(raise_error) and self.expr2.supported_by_actionD(raise_error)

    def is_boolean(self):
        if self.op in (nmlop.AND, nmlop.OR, nmlop.XOR):
            return self.expr1.is_boolean() and self.expr2.is_boolean()
        return self.op.returns_boolean

class TernaryOp(Expression):
    def __init__(self, guard, expr1, expr2, pos):
        Expression.__init__(self, pos)
        self.guard = guard
        self.expr1 = expr1
        self.expr2 = expr2

    def debug_print(self, indentation):
        print indentation*' ' + 'Ternary operator'
        print indentation*' ' + 'Guard:'
        self.guard.debug_print(indentation + 2)
        print indentation*' ' + 'Expression 1:'
        self.expr1.debug_print(indentation + 2)
        print indentation*' ' + 'Expression 2:'
        self.expr2.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        guard = self.guard.reduce(id_dicts)
        expr1 = self.expr1.reduce(id_dicts)
        expr2 = self.expr2.reduce(id_dicts)
        if isinstance(guard, ConstantNumeric):
            if guard.value != 0:
                return expr1
            else:
                return expr2
        if guard.type() != Type.INTEGER or expr1.type() != Type.INTEGER or expr2.type() != Type.INTEGER:
            raise generic.ScriptError("All parts of the ternary operator (?:) must be integers.", self.pos)
        return TernaryOp(guard, expr1, expr2, self.pos)

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        return True

    def is_boolean(self):
        return self.expr1.is_boolean() and self.expr2.is_boolean()

    def __str__(self):
        return "(%s ? %s : %s)" % (str(self.guard), str(self.expr1), str(self.expr2))

class Boolean(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Force expression to boolean:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Only integers can be converted to a boolean value.", self.pos)
        if expr.is_boolean(): return expr
        return Boolean(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

    def __str__(self):
        return "(bool)" + str(self.expr)

class BinNot(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Binary not:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Not-operator (~) requires an integer argument.", expr.pos)
        if isinstance(expr, ConstantNumeric): return ConstantNumeric(0xFFFFFFFF ^ expr.value)
        if isinstance(expr, BinNot): return expr.expr
        return BinNot(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def __str__(self):
        return "~" + str(self.expr)

class Not(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Logical not:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Not-operator (!) requires an integer argument.", expr.pos)
        if isinstance(expr, ConstantNumeric): return ConstantNumeric(expr.value != 0)
        if isinstance(expr, Not): return expr.expr
        if isinstance(expr, BinOp):
            if expr.op == nmlop.CMP_EQ: return BinOp(nmlop.CMP_NEQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_NEQ: return BinOp(nmlop.CMP_EQ, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LE: return BinOp(nmlop.CMP_GT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GE: return BinOp(nmlop.CMP_LT, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_LT: return BinOp(nmlop.CMP_GE, expr.expr1, expr.expr2)
            if expr.op == nmlop.CMP_GT: return BinOp(nmlop.CMP_LE, expr.expr1, expr.expr2)
            if expr.op == nmlop.HASBIT: return BinOp(nmlop.NOTHASBIT, expr.expr1, expr.expr2)
            if expr.op == nmlop.NOTHASBIT: return BinOp(nmlop.HASBIT, expr.expr1, expr.expr2)
        return Not(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

    def __str__(self):
        return "!" + str(self.expr)

class Parameter(Expression):
    def __init__(self, num, pos = None):
        Expression.__init__(self, pos)
        self.num = num

    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return 'param[%s]' % str(self.num)

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

class OtherGRFParameter(Expression):
    def __init__(self, grfid, num, pos = None):
        Expression.__init__(self, pos)
        self.grfid = grfid
        self.num = num
        if not isinstance(self.grfid, int):
            if not isinstance(self.grfid, StringLiteral) or grfstrings.get_string_size(self.grfid.value, False, True) != 4:
                raise generic.ScriptError("GRFID must be string literal of length 4", self.grfid.pos)
            self.grfid = generic.parse_string_to_dword(self.grfid)

    def debug_print(self, indentation):
        print indentation*' ' + 'OtherGRFParameter:'
        self.grfid.debug_print(indentation + 2)
        self.num.debug_print(indentation + 2)

    def __str__(self):
        return 'param[%s, %s]' % (str(self.grfid), str(self.num))

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        num = self.num.reduce(id_dicts)
        if num.type() != Type.INTEGER:
            raise generic.ScriptError("Parameter number must be an integer.", num.pos)
        return OtherGRFParameter(self.grfid, num, self.pos)

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Reading parameters from another GRF is not supported in a switch-block.", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        return True

class PatchVariable(Expression):
    """
    Class for reading so-called 'patch variables' via a special ActionD

    @ivar num: Variable number to read
    @type num: C{int}
    """
    def __init__(self, num, pos = None):
        Expression.__init__(self, pos)
        self.num = num

    def debug_print(self, indentation):
        print indentation*' ' + 'PatchVariable: ' + str(self.num)

    def __str__(self, indentation):
        return "PatchVariable(%d)" % self.num

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def supported_by_action2(self, raise_error):
        if raise_error:
            raise generic.ScriptError("Reading patch variables is not supported in a switch-block.", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        return True

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
        ret = 'var[%s, %s, %s' % (str(self.num), str(self.shift), str(self.mask))
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

class FunctionPtr(Expression):
    """
    Pointer to a function.
    If this appears inside an expression, the user has made an error.

    @ivar name Identifier that has been resolved to this function pointer.
    @type name L{Identifier}

    @ivar func Function that will be called to resolve this function call. Arguments:
                    Name of the function (C{basestring})
                    List of passed arguments (C{list} of L{Expression})
                    Position information (L{Position})
                    Any extra arguments passed to the constructor of this class
    @type func C{function}

    @ivar extra_args List of arguments that should be passed to the function that is to be called.
    @type extra_args C{list}
    """
    def __init__(self, name, func, *extra_args):
        self.name = name
        self.func = func
        self.extra_args = extra_args

    def debug_print(self, indentation):
        assert False, "Function pointers should not appear inside expressions."

    def __str__(self):
        assert False, "Function pointers should not appear inside expressions."

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        raise generic.ScriptError("'%s' is a function and should be called using the function call syntax." % str(self.name), self.name.pos)

    def type(self):
        return Type.FUNCTION_PTR

    def call(self, args):
        return self.func(self.name.value, args, self.name.pos, *self.extra_args)

class FunctionCall(Expression):
    def __init__(self, name, params, pos):
        Expression.__init__(self, pos)
        self.name = name
        self.params = params

    def debug_print(self, indentation):
        print indentation*' ' + 'Call function: ' + self.name.value
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = ''
        for param in self.params:
            if ret == '': ret = str(param)
            else: ret = '%s, %s' % (ret, str(param))
        ret = '%s(%s)' % (self.name, ret)
        return ret

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        param_list = []
        for param in self.params:
            param_list.append(param.reduce(id_dicts, unknown_id_fatal))
        if self.name.value in function_table:
            func = function_table[self.name.value]
            val = func(self.name.value, param_list, self.pos)
            return val.reduce(id_dicts)
        else:
            #try user-defined functions
            func_ptr = self.name.reduce(id_dicts, False, True)
            if func_ptr != self.name: # we found something!
                if func_ptr.type() != Type.FUNCTION_PTR:
                    raise generic.ScriptError("'%s' is defined, but it is not a function." % self.name.value, self.pos)
                return func_ptr.call(param_list)
            if unknown_id_fatal:
                raise generic.ScriptError("'%s' is not defined as a function." % self.name.value, self.pos)
            return FunctionCall(self.name, param_list, self.pos)

class String(Expression):
    def __init__(self, name, params, pos):
        Expression.__init__(self, pos)
        self.name = name
        self.params = params

    def debug_print(self, indentation):
        print indentation*' ' + 'String:'
        self.name.debug_print(indentation + 2)
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)

    def __str__(self):
        ret = 'string(' + self.name.value
        for p in self.params:
            ret += ', ' + str(p)
        ret += ')'
        return ret

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

class Identifier(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'ID: ' + self.value

    def __str__(self):
        return self.value

    def reduce(self, id_dicts = [], unknown_id_fatal = True, search_func_ptr = False):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x, pos: StringLiteral(x, pos) if isinstance(x, basestring) else ConstantNumeric(x, pos)) if not isinstance(id_dict, tuple) else id_dict
            if self.value in id_d:
                if search_func_ptr:
                    # XXX - hacky
                    # Call func with (name, value) instead of (value, name)
                    # And do not reduce the resulting value
                    return func(self, id_d[self.value])
                else:
                    return func(id_d[self.value], self.pos).reduce(id_dicts)
        if unknown_id_fatal: raise generic.ScriptError("Unrecognized identifier '" + self.value + "' encountered", self.pos)
        return self

    def supported_by_actionD(self, raise_error):
        if raise_error: raise generic.ScriptError("Unknown identifier '%s'" % self.value, self.pos)
        return False

class StringLiteral(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'String literal: "%s"' % self.value

    def __str__(self):
        return '"%s"' % self.value

    def write(self, file, size):
        assert(len(self.value) == size)
        file.print_string(self.value, final_zero = False, force_ascii = True)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def type(self):
        return Type.STRING_LITERAL

class Array(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Array of values:'
        for v in self.values:
            v.debug_print(indentation + 2)

    def __str__(self):
        return '[' + ', '.join([str(expr) for expr in self.values]) + ']'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return Array([val.reduce(id_dicts, unknown_id_fatal) for val in self.values], self.pos)

class SpecialCheck(Expression):
    """
    Action7/9 special check (e.g. to see whether a cargo is defined)

    @ivar op: Action7/9 operator to use
    @type op: (C{int}, C{basestring})-tuple

    @ivar varnum: Variable number to read
    @type varnum: C{int}

    @ivar results: Result of the check when skipping (0) or not skipping (1)
    @type results: (C{int}, C{int})-tuple

    @ivar value: Value to test
    @type value: C{int}

    @ivar mask: Mask to to test only certain bits of the value
    @type mask: C{int}

    @ivar pos: Position information
    @type pos: L{Position}
    """
    def __init__(self, op, varnum, results, value, mask = None, pos = None):
        Expression.__init__(self, pos)
        self.op = op
        self.varnum = varnum
        self.results = results
        self.value = value
        self.mask = mask

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def __str__(self):
        return 'SpecialCheck'

    def supported_by_actionD(self, raise_error):
        return True

class SpecialParameter(Expression):
    """
    Class for handling special grf parameters.
    These can be assigned special, custom methods for reading / writing to them.

    @ivar name: Name of the parameter, for debugging purposes
    @type name: C{basestring}

    @ivar info: Information about the parameter
    @type info: C{dict}

    @ivar write_func: Function that will be called when the parameter is the target of an assignment
                        Arguments:
                            Dictionary with parameter information (self.info)
                            Target expression to assign
                            Position information
                        Return value is a 2-tuple:
                            Left side of the assignment (must be a parameter)
                            Right side of the assignment (may be any expression)
    @type write_func: C{function}

    @ivar read_func: Function that will be called to read out the parameter value
                        Arguments:
                            Dictionary with parameter information (self.info)
                            Position information
                        Return value:
                            Expression that should be evaluated to get the parameter value
    @type read_func: C{function}

    @ivar is_bool: Does read_func return a boolean value?
    @type is_bool: C{bool}
    """

    def __init__(self, name, info, write_func, read_func, is_bool, pos = None):
        Expression.__init__(self, pos)
        self.name = name
        self.info = info
        self.write_func = write_func
        self.read_func = read_func
        self.is_bool = is_bool

    def debug_print(self, indentation):
        print indentation*' ' + "Special parameter '%s'" % self.name

    def __str__(self):
        return self.name

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def is_boolean(self):
        return self.is_bool

    def can_assign(self):
        return self.write_func is not None

    def to_assignment(self, expr):
        param, expr = self.write_func(self.info, expr, self.pos)
        param = param.reduce()
        expr = expr.reduce()
        return (param, expr)

    def to_reading(self):
        param = self.read_func(self.info, self.pos)
        param = param.reduce()
        return param

    def supported_by_actionD(self, raise_error):
        return True

    def supported_by_action2(self, raise_error):
        return True

#{ Builtin functions

def builtin_min(name, args, pos):
    """
    min(...) builtin function.

    @return Lowest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("min() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(nmlop.MIN, x, y, pos), args)

def builtin_max(name, args, pos):
    """
    max(...) builtin function.

    @return Heighest value of the given arguments.
    """
    if len(args) < 2:
        raise generic.ScriptError("max() requires at least 2 arguments", pos)
    return reduce(lambda x, y: BinOp(nmlop.MAX, x, y, pos), args)

def builtin_date(name, args, pos):
    """
    date(year, month, day) builtin function.

    @return Days since 1 jan 1 of the given date.
    """
    if len(args) != 3:
        raise generic.ScriptError("date() requires exactly 3 arguments", pos)
    year = args[0].reduce()
    try:
        month = args[1].reduce_constant().value
        day = args[2].reduce_constant().value
    except generic.ConstError:
        raise generic.ScriptError("Month and day parameters of date() should be compile-time constants", pos)
    if not isinstance(year, ConstantNumeric):
        if month != 1 or day != 1:
            raise generic.ScriptError("when the year parameter of date() is not a compile time constant month and day should be 1", pos)
        #num_days = year*365 + year/4 - year/100 + year/400
        part1 = BinOp(nmlop.MUL, year, ConstantNumeric(365))
        part2 = BinOp(nmlop.DIV, year, ConstantNumeric(4))
        part3 = BinOp(nmlop.DIV, year, ConstantNumeric(100))
        part4 = BinOp(nmlop.DIV, year, ConstantNumeric(400))
        res = BinOp(nmlop.ADD, part1, part2)
        res = BinOp(nmlop.SUB, res, part3)
        res = BinOp(nmlop.ADD, res, part4)
        return res
    date = datetime.date(year.value, month, day)
    return ConstantNumeric(year.value * 365 + calendar.leapdays(0, year.value) + date.timetuple().tm_yday - 1, pos)

def builtin_day_of_year(name, args, pos):
    """
    day_of_year(month, day) builtin function.

    @return Day of the year, assuming February has 28 days.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have a month and a day parameter", pos)

    month = args[0].reduce()
    if not isinstance(month, ConstantNumeric):
        raise generic.ScriptError('Month should be a compile-time constant.', month.pos)
    if month.value < 1 or month.value > 12:
        raise generic.ScriptError('Month should be a value between 1 and 12.', month.pos)

    day = args[0].reduce()
    if not isinstance(day, ConstantNumeric):
        raise generic.ScriptError('Day should be a compile-time constant.', day.pos)

    # Mapping of month to number of days in that month.
    number_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if day.value < 1 or day.value > number_days[month.value]:
        raise generic.ScriptError('Day should be value between 1 and %d.' % number_days[month.value], day.pos)

    return ConstantNumeric(datetime.date(1, month.value, day.value).toordinal(), pos)


def builtin_store(name, args, pos):
    """
    STORE_TEMP(value, register) builtin function.
    STORE_PERM(value, register) builtin function.
    Store C{value} in temporary/permanent storage in location C{register}.

    @return C{value}
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    op = nmlop.STO_TMP if name == 'STORE_TEMP' else nmlop.STO_PERM
    return BinOp(op, args[0], args[1], pos)

def builtin_load(name, args, pos):
    """
    LOAD_TEMP(register) builtin function.
    LOAD_PERM(register) builtin function.
    Load a value from location C{register} from temporary/permanent storage.

    @return The value loaded from the storage.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have one parameter", pos)
    var_num = 0x7D if name == "LOAD_TEMP" else 0x7C
    return Variable(ConstantNumeric(var_num), param=args[0], pos=pos)

def builtin_hasbit(name, args, pos):
    """
    hasbit(value, bit_num) builtin function.

    @return C{1} if and only if C{value} has bit C{bit_num} set, C{0} otherwise.
    """
    if len(args) != 2:
        raise generic.ScriptError(name + "() must have exactly two parameters", pos)
    return BinOp(nmlop.HASBIT, args[0], args[1], pos)

def builtin_version_openttd(name, args, pos):
    """
    version_openttd(major, minor, revision[, build]) builtin function.

    @return The version information encoded in a double-word.
    """
    if len(args) > 4 or len(args) < 3:
        raise generic.ScriptError(name + "() must have 3 or 4 parameters", pos)
    major = args[0].reduce_constant().value
    minor = args[1].reduce_constant().value
    revision = args[2].reduce_constant().value
    build = args[3].reduce_constant().value if len(args) == 4 else 0x80000
    return ConstantNumeric((major << 28) | (minor << 24) | (revision << 20) | build)

def builtin_cargotype_available(name, args, pos):
    """
    cargotype_available(cargo_label) builtin function.

    @return 1 if the cargo label is available, 0 otherwise.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have exactly 1 parameter", pos)
    label = args[0].reduce()
    if not isinstance(label, StringLiteral) or grfstrings.get_string_size(label.value, False, True) != 4:
        raise generic.ScriptError("Cargo labels must be string literals of length 4", label.pos)
    return SpecialCheck((0x0B, r'\7c'), 0, (0, 1), generic.parse_string_to_dword(label), None, args[0].pos)

def builtin_railtype_available(name, args, pos):
    """
    railtype_available(cargo_label) builtin function.

    @return 1 if the railtype label is available, 0 otherwise.
    """
    if len(args) != 1:
        raise generic.ScriptError(name + "() must have exactly 1 parameter", pos)
    label = args[0].reduce()
    if not isinstance(label, StringLiteral) or grfstrings.get_string_size(label.value, False, True) != 4:
        raise generic.ScriptError("Railtype labels must be string literals of length 4", label.pos)
    return SpecialCheck((0x0D, None), 0, (0, 1), generic.parse_string_to_dword(label), None, args[0].pos)

def builtin_grf_status(name, args, pos):
    """
    grf_(current|future)_status(grfid[, mask]) builtin function.

    @return 1 if the grf is, or will be, active, 0 otherwise.
    """
    if len(args) not in (1, 2):
        raise generic.ScriptError(name + "() must have 1 or 2 parameters", pos)
    labels = []
    for label in args:
        label = label.reduce()
        if not isinstance(label, StringLiteral) or grfstrings.get_string_size(label.value, False, True) != 4:
            raise generic.ScriptError("GRFIDs must be string literals of length 4", label.pos)
        labels.append(label)
    if name == 'grf_current_status':
        op = (0x06, r'\7G')
        results = (1, 0)
    elif name == 'grf_future_status':
        op = (0x0A, r'\7gg')
        results = (0, 1)
    else:
        assert False, "Unknown grf status function"
    mask = generic.parse_string_to_dword(labels[1]) if len(labels) > 1 else None
    return SpecialCheck(op, 0x88, results, generic.parse_string_to_dword(labels[0]), mask, args[0].pos)

def builtin_visual_effect_and_powered(name, args, pos):
    """
    visual_effect_and_powered(effect, offset, powered) builtin function. Use this to set
    the train property visual_effect_and_powered and for the callback VEH_CB_VISUAL_EFFECT_AND_POWERED
    """
    if len(args) != 3:
        raise generic.ScriptError(name + "() must have 3 parameters", pos)
    from nml import global_constants
    effect = args[0].reduce_constant([global_constants.item_names]).value
    offset = BinOp(nmlop.ADD, args[1], ConstantNumeric(8), args[1].pos).reduce_constant().value
    generic.check_range(offset, 0, 0x0F, "offset in function visual_effect_and_powered", pos)
    powered = args[2].reduce_constant([global_constants.item_names]).value
    if powered != 0 and powered != 0x80:
        raise generic.ScriptError("3rd argument to visual_effect_and_powered (powered) must be either ENABLE_WAGON_POWER or DISABLE_WAGON_POWER", pos)
    return ConstantNumeric(effect | offset | powered)
#}

function_table = {
    'min' : builtin_min,
    'max' : builtin_max,
    'date' : builtin_date,
    'day_of_year' : builtin_day_of_year,
    'bitmask' : lambda name, args, pos: BitMask(args, pos),
    'STORE_TEMP' : builtin_store,
    'STORE_PERM' : builtin_store,
    'LOAD_TEMP' : builtin_load,
    'LOAD_PERM' : builtin_load,
    'hasbit' : builtin_hasbit,
    'version_openttd' : builtin_version_openttd,
    'cargotype_available' : builtin_cargotype_available,
    'railtype_available' : builtin_railtype_available,
    'grf_current_status' : builtin_grf_status,
    'grf_future_status' : builtin_grf_status,
    'visual_effect_and_powered' : builtin_visual_effect_and_powered,
}

commutative_operators = set([
    nmlop.ADD,
    nmlop.MUL,
    nmlop.AND,
    nmlop.OR,
    nmlop.XOR,
    nmlop.CMP_EQ,
    nmlop.CMP_NEQ,
    nmlop.MIN,
    nmlop.MAX,
])
