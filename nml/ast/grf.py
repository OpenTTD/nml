from nml import expression, generic
from nml.actions import action8, action14

class GRF(object):
    def __init__(self, alist, pos):
        self.pos = pos
        self.name = None
        self.desc = None
        self.grfid = None
        for assignment in alist:
            if assignment.name.value == "name": self.name = assignment.value
            elif assignment.name.value == "desc": self.desc = assignment.value
            elif assignment.name.value == "grfid": self.grfid = assignment.value
            else: raise generic.ScriptError("Unknown item in GRF-block: " + str(assignment.name), assignment.name.pos)

    def pre_process(self):
        self.grfid = self.grfid.reduce()
        if not isinstance(self.grfid, expression.StringLiteral):
            raise generic.ScriptError("GRFID must be a string literal", self.grfid.pos)
        self.name = self.name.reduce()
        if not isinstance(self.name, expression.String):
            raise generic.ScriptError("GRF-name must be a string", self.name.pos)
        self.desc = self.desc.reduce()
        if not isinstance(self.desc, expression.String):
            raise generic.ScriptError("GRF-description must be a string", self.desc.pos)

    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        if self.grfid is not None:
            print (2+indentation)*' ' + 'grfid:', self.grfid.value
        if self.name is not None:
            print (2+indentation)*' ' + 'Name:'
            self.name.debug_print(indentation + 4)
        if self.desc is not None:
            print (2+indentation)*' ' + 'Description:'
            self.desc.debug_print(indentation + 4)

    def get_action_list(self):
        return action14.grf_name_desc_actions(self.name, self.desc) + [action8.Action8(self.grfid, self.name, self.desc)]

    def __str__(self):
        ret = 'grf {\n'
        ret += '\tgrfid: %s;\n' % str(self.grfid)
        if self.name is not None:
            ret += '\tname: %s;\n' % str(self.name)
        if self.desc is not None:
            ret += '\tdesc: %s;\n' % str(self.desc)
        ret += '}\n'
        return ret

class Assignment(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)
