import ast
from action6 import *

class ActionDOperator:
    EQUAL = r'\D='
    ADD   = r'\D+'
    SUB   = r'\D-'
    MULU  = r'\Du*'
    MULS  = r'\D*'
    SHFTU = r'\Du<<'
    SHFTS = r'\D<<'
    AND   = r'\D&'
    OR    = r'\D|'
    DIVU  = r'\Du/'
    DIVS  = r'\D/'
    MODU  = r'\Du%'
    MODS  = r'\D%'

class ActionD:
    def __init__(self, target, param1, op, param2, data = None):
        self.target = target
        self.param1 = param1
        self.op = op
        self.param2 = param2
        self.data = data
    
    def write(self, file):
        file.write("-1 * 0 0D ")
        self.target.write(file, 1)
        file.write(self.op + " ")
        self.param1.write(file, 1)
        self.param2.write(file, 1)
        if self.data != None: self.data.write(file, 4)
        file.write("\n\n")
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return True
    
    def skip_needed(self):
        return True

def convert_op_to_actiond(op):
    if op == ast.Operator.ADD: return ActionDOperator.ADD
    if op == ast.Operator.SUB: return ActionDOperator.SUB
    if op == ast.Operator.AND: return ActionDOperator.AND
    if op == ast.Operator.OR: return ActionDOperator.OR
    raise ast.ScriptError("Unsupported operator in parameter assignment: " + str(op))

#returns a (param_num, action_list) tuple.
def get_tmp_parameter(expr):
    param = free_parameters.pop()
    actions = parse_actionD(ast.ParameterAssignment(ast.ConstantNumeric(param), expr))
    return (param, actions)

def parse_actionD(assignment):
    global free_parameters
    free_parameters_backup = free_parameters[:]
    action_list = []
    action6 = Action6()
    target = assignment.param
    if isinstance(target, ast.Parameter) and isinstance(target.num, ast.ConstantNumeric):
        action6.modify_bytes(target.num.value, 1, 1)
        target = ast.ConstantNumeric(0)
    elif not isinstance(target, ast.ConstantNumeric):
        tmp_param, tmp_param_actions = get_tmp_parameter(target)
        action6.modify_bytes(tmp_param, 1, 1)
        target = ast.ConstantNumeric(0)
        action_list.extend(tmp_param_actions)
    
    data = None
    #print assignment.value
    if isinstance(assignment.value, ast.ConstantNumeric):
        op = ActionDOperator.EQUAL
        param1 = ast.ConstantNumeric(0xFF)
        param2 = ast.ConstantNumeric(0)
        data = assignment.value
    elif isinstance(assignment.value, ast.Parameter):
        if isinstance(assignment.value.num, ast.ConstantNumeric):
            op = ActionDOperator.EQUAL
            param1 = assignment.value.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(assignment.value.num)
            action6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            op = ActionDOperator.EQUAL
            param1 = ast.ConstantNumeric(0)
        param2 = ast.ConstantNumeric(0)
    elif isinstance(assignment.value, ast.BinOp):
        expr = assignment.value
        op = convert_op_to_actiond(expr.op)
        
        if isinstance(expr.expr1, ast.ConstantNumeric):
            param1 = ast.ConstantNumeric(0xFF)
            data = expr.expr1
        elif isinstance(expr.expr1, ast.Parameter):
            param1 = expr.expr1.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr1)
            action6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            param1 = ast.ConstantNumeric(0)
        
        # We can use the data only for one for the parameters.
        # If the first parameter uses "data" we need a temp parameter for this one
        if isinstance(expr.expr2, ast.ConstantNumeric) and data == None:
            param2 = ast.ConstantNumeric(0xFF)
            data = expr.expr2
        elif isinstance(expr.expr2, ast.Parameter):
            param2 = expr.expr2.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr2)
            action6.modify_bytes(tmp_param, 1, 4)
            action_list.extend(tmp_param_actions)
            param2 = ast.ConstantNumeric(0)
        
    else: raise ast.ScriptError("Invalid expression in argument assignment")
    
    if len(action6.modifications) > 0: action_list.append(action6)
    
    action_list.append(ActionD(target, param1, op, param2, data))
    free_parameters = free_parameters_backup
    return action_list
