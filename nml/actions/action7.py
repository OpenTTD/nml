from nml.expression import *
from action6 import *
from nml.actions import actionD, action10

#a jump is always to the next action10 with a given id, so they
#can be freely reused
free_labels = range(0x10, 0x70)
free_labels.reverse()
#for a loop we need to jump backward, so those labels can't be reused
free_while_labels = range(0x80, 0x100)
free_while_labels.reverse()

class SkipAction(object):
    def __init__(self, feature, var, varsize, condtype, value, label):
        self.feature = feature
        self.label = label
        self.var = var
        self.varsize = varsize
        self.condtype = condtype
        self.value = value
        self.label = label

    def prepare_output(self):
        pass

    def write(self, file):
        size = 5 + self.varsize
        file.print_sprite_size(size)
        file.print_bytex(self.feature)
        file.print_bytex(self.var)
        file.print_bytex(self.varsize)
        file.print_bytex(self.condtype[0], self.condtype[1])
        file.print_varx(self.value, self.varsize)
        file.print_bytex(self.label)
        file.newline()
        file.newline()

    def skip_action7(self):
        return self.feature == 7

    def skip_action9(self):
        return self.feature == 9 or self.label == 0

    def skip_needed(self):
        return True

class UnconditionalSkipAction(SkipAction):
    def __init__(self, feature, label):
        SkipAction.__init__(self, feature, 0x83, 1, (3, r'\7! '), 0xFF, label)

def op_to_cond_op(op):
    #The operators are reversed as we want to skip if the expression is true
    #while the nml-syntax wants to execute the block if the expression is true
    if op == Operator.CMP_NEQ: return (2, r'\7=')
    if op == Operator.CMP_EQ: return (3, r'\7!')
    if op == Operator.CMP_GT: return (4, r'\7<')
    if op == Operator.CMP_LT: return (5, r'\7>')

def parse_conditional(expr):
    '''Parse an expression and return enougn information to use
    that expression as a conditional statement.
    Return value is a tuple with the following elements:
    - Parameter number (as integer) to use in comparison or None for unconditional skip
    - List of actions needed to set the given parameter to the correct value
    - The type of comparison to be done
    - The value to compare against (as integer)
    '''
    if expr is None:
        return (None, [], (2, r'\7='), 0)
    if isinstance(expr, BinOp) and expr.op in (Operator.CMP_EQ, Operator.CMP_NEQ, Operator.CMP_LT, Operator.CMP_GT) \
            and isinstance(expr.expr2, ConstantNumeric):
        if isinstance(expr.expr1, Parameter) and isinstance(expr.expr1.num, ConstantNumeric):
            param = expr.expr1.num.value
            actions = []
        else:
            param, actions = actionD.get_tmp_parameter(expr.expr1)
        op = op_to_cond_op(expr.op)
        return (param, actions, op, expr.expr2.value)
    else:
        param, actions = actionD.get_tmp_parameter(expr)
        return (param, actions, (2, r'\7='), 0)

def cond_skip_actions(action_list, param, condtype, value):
    actions = []
    start, length = 0, 0
    allow7, allow9 = True, True
    for i in range(0, len(action_list)):
        action = action_list[i]
        if length == 0 and not action.skip_needed():
            actions.append(action)
            start += 1
            continue
        length += 1
        if allow7 and action.skip_action7():
            allow9 = allow9 and action.skip_action9()
            continue
        if allow9 and action.skip_action9():
            #if action7 was ok, we wouldn't be in this block
            allow7 = False
            continue
        #neither action7 nor action9 can be used. add all
        #previous actions to the list and start a new block
        feature = 7 if allow7 else 9
        if length < 0x10:
            target = length
            label = None
        else:
            target = free_labels.pop()
            label = action10.Action10(target)
        actions.append(SkipAction(feature, param, 4, condtype, value, target))
        actions.extend(action_list[start:start+length])
        if label is not None: actions.append(label)
        start = i + 1
        length = 0
        allow7, allow9 = True, True

    if length > 0:
        feature = 7 if allow7 else 9
        if length < 0x10:
            target = length
            label = None
        else:
            target = free_labels.pop()
            label = action10.Action10(target)
        actions.append(SkipAction(feature, param, 4, condtype, value, target))
        actions.extend(action_list[start:start+length])
        if label is not None: actions.append(label)
    return actions

def parse_conditional_block(cond):
    global free_parameters, free_labels
    free_parameters_backup = free_parameters[:]
    free_labels_backup = free_labels[:]

    multiple_blocks = cond.else_block is not None
    if multiple_blocks:
        #the skip all parameter is used to skip all blocks after one
        #of the conditionals was true. We can't always skip directly
        #to the end of the blocks since action7/action9 can't always
        #be mixed
        param_skip_all, action_list = actionD.get_tmp_parameter(ConstantNumeric(0xFFFFFFFF))
    else:
        action_list = []

    blocks = []
    while cond is not None:
        end_label = free_labels.pop()
        blocks.append({'expr': cond.expr, 'statements': cond.block, 'last_block': cond.else_block is None})
        cond = cond.else_block

    #use parse_conditional here, we also need to know if all generated
    #actions (like action6) can be skipped safely
    for block in blocks:
        block['param_dst'], block['cond_actions'], block['cond_type'], block['cond_value'] = parse_conditional(block['expr'])
        if not block['last_block']:
            block['action_list'] = [actionD.ActionD(ConstantNumeric(param_skip_all), ConstantNumeric(0xFF), actionD.ActionDOperator.EQUAL, ConstantNumeric(0), ConstantNumeric(0))]
        else:
            block['action_list'] = []
        for stmt in block['statements']:
            block['action_list'].extend(stmt.get_action_list())

    #Main problem: action10 can't be skipped by action9, so we're
    #nearly forced to use action7, but action7 can't safely skip action6
    #Solution: use temporary parameter, set to 0 for not skip, !=0 for skip.
    #then skip every block of actions (as large as possible) with either
    #action7 or action9, depending on which of the two works.

    for i in range(0, len(blocks)):
        block = blocks[i]
        param = block['param_dst']
        if i == 0: action_list.extend(block['cond_actions'])
        else:
            action_list.extend(cond_skip_actions(block['cond_actions'], param_skip_all, (2, r'\7='), 0))
            if param is None:
                param = param_skip_all
            else:
                action_list.append(actionD.ActionD(ConstantNumeric(block['param_dst']), ConstantNumeric(block['param_dst']), actionD.ActionDOperator.AND, ConstantNumeric(param_skip_all)))
        action_list.extend(cond_skip_actions(block['action_list'], param, block['cond_type'], block['cond_value']))

    free_labels.extend([item for item in free_labels_backup if not item in free_labels])
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list

def parse_loop_block(loop):
    global free_parameters, free_labels, free_while_labels
    free_parameters_backup = free_parameters[:]
    free_labels_backup = free_labels[:]
    begin_label = free_while_labels.pop()
    action_list = [action10.Action10(begin_label)]

    cond_param, cond_actions, cond_type, cond_value = parse_conditional(loop.expr)
    block_actions = []
    for stmt in loop.block:
        block_actions.extend(stmt.get_action_list())

    action_list.extend(cond_actions)
    block_actions.append(UnconditionalSkipAction(9, begin_label))
    action_list.extend(cond_skip_actions(block_actions, cond_param, (2, r'\7='), 0))

    free_labels.extend([item for item in free_labels_backup if not item in free_labels])
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
