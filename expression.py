from generic import *

class Operator:
    ADD     = 0
    SUB     = 1
    DIV     = 2
    MOD     = 3
    MUL     = 4
    AND     = 5
    OR      = 6
    XOR     = 7
    VAL2    = 8
    CMP_EQ  = 9
    CMP_NEQ = 10
    CMP_LT  = 11
    CMP_GT  = 12
    MIN     = 13
    MAX     = 14
    STO_TMP = 15
    STO_PERM = 16

class ConstantNumeric:
    def __init__(self, value):
        self.value = truncate_int32(value)
    def debug_print(self, indentation):
        print indentation*' ' + 'Int:', self.value
    def write(self, file, size):
        print_varx(file, self.value, size)

class BinOp:
    def __init__(self, op, expr1, expr2):
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Binary operator, op = ', self.op
        if isinstance(self.expr1, str):
            print (indentation+2)*' ' + 'ID:', self.expr1
        else:
            self.expr1.debug_print(indentation + 2)
        if isinstance(self.expr2, str):
            print (indentation+2)*' ' + 'ID:', self.expr2
        else:
            self.expr2.debug_print(indentation + 2)

class TernaryOp:
    def __init__(self, guard, expr1, expr2):
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

class Assignment:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)

class Parameter:
    def __init__(self, num):
        self.num = num
    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter:'
        self.num.debug_print(indentation + 2)

class Variable:
    def __init__(self, num, shift = None, mask = None, param = None):
        self.num = num
        self.shift = shift if shift != None else ConstantNumeric(0)
        self.mask = mask if mask != None else ConstantNumeric(0xFFFFFFFF)
        self.param = param
        self.add = None
        self.div = None
        self.mod = None
    
    def debug_print(self, indentation):
        print indentation*' ' + 'Action2 variable'
        self.num.debug_print(indentation + 2)
        if self.param != None:
            print (indentation+2)*' ' + 'Parameter:'
            if isinstance(self.param, str):
                print (indentation+4)*' ' + 'Procedure call:', self.param
            else:
                self.param.debug_print(indentation + 4)

class String:
    def __init__(self, name, params = []):
        self.name = name
        self.params = params
    def debug_print(self, indentation):
        print indentation*' ' + 'String: ' + self.name
        for param in self.params:
            print (indentation+2)*' ' + 'Parameter:'
            param.debug_print(indentation + 4)