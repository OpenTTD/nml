from nml import expression, generic, grfstrings, global_constants
from nml.actions import action8, action14

palette_node = None

def set_palette_used(pal):
    if palette_node:
        palette_node.pal = pal

class GRF(object):
    def __init__(self, alist, pos):
        self.pos = pos
        self.name = None
        self.desc = None
        self.grfid = None
        self.version = None
        self.params = []
        generic.OnlyOnce.enforce(self, "GRF-block")
        for assignment in alist:
            if isinstance(assignment, ParameterDescription):
                self.params.append(assignment)
            elif assignment.name.value == "name": self.name = assignment.value
            elif assignment.name.value == "desc": self.desc = assignment.value
            elif assignment.name.value == "grfid": self.grfid = assignment.value
            elif assignment.name.value == "version": self.version = assignment.value
            else: raise generic.ScriptError("Unknown item in GRF-block: " + str(assignment.name), assignment.name.pos)
        if None in (self.name, self.desc, self.grfid, self.version):
            raise generic.ScriptError("A GRF-block requires the 'name', 'desc', 'grfid', and 'version' properties to be set.", self.pos)

    def pre_process(self):
        self.grfid = self.grfid.reduce()
        if not isinstance(self.grfid, expression.StringLiteral) or grfstrings.get_string_size(self.grfid.value, False, True) != 4:
            raise generic.ScriptError("GRFID must be a string literal of length 4", self.grfid.pos)
        global_constants.constant_numbers['GRFID'] = generic.parse_string_to_dword(self.grfid.value)
        self.name = self.name.reduce()
        if not isinstance(self.name, expression.String):
            raise generic.ScriptError("GRF-name must be a string", self.name.pos)
        self.desc = self.desc.reduce()
        if not isinstance(self.desc, expression.String):
            raise generic.ScriptError("GRF-description must be a string", self.desc.pos)
        self.version = self.version.reduce_constant()
        param_num = 0
        for param in self.params:
            param.pre_process(expression.ConstantNumeric(param_num))
            param_num = param.num.value + 1

    def debug_print(self, indentation):
        print indentation*' ' + 'GRF'
        print (2+indentation)*' ' + 'grfid:'
        self.grfid.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Name:'
        self.name.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Description:'
        self.desc.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Version:'
        self.version.debug_print(indentation + 4)

    def get_action_list(self):
        global palette_node
        palette_node = action14.UsedPaletteNode("A")
        action14_root = action14.BranchNode("INFO")
        action14.grf_name_desc_actions(action14_root, self.name, self.desc, self.version)
        action14.param_desc_actions(action14_root, self.params)
        action14_root.subnodes.append(palette_node)
        return action14.get_actions(action14_root) + [action8.Action8(self.grfid, self.name, self.desc)]

    def __str__(self):
        ret = 'grf {\n'
        ret += '\tgrfid: %s;\n' % str(self.grfid)
        if self.name is not None:
            ret += '\tname: %s;\n' % str(self.name)
        if self.desc is not None:
            ret += '\tdesc: %s;\n' % str(self.desc)
        ret += '}\n'
        return ret

class SettingValue(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class NameValue(object):
    def __init__(self, num, desc):
        self.num = num
        self.desc = desc

class ParameterSetting(object):
    def __init__(self, name, value_list):
        self.name = name
        self.value_list = value_list
        self.type = 'int'
        self.name_string = None
        self.desc_string = None
        self.min_val = None
        self.max_val = None
        self.def_val = None
        self.bit_num = None
        self.val_names = []
        self.properties_set = set()

    def pre_process(self):
        for set_val in self.value_list:
            self.set_property(set_val.name.value, set_val.value)

    def set_property(self, name, value):
        if name in self.properties_set:
            raise generic.ScriptError("You cannot set the same property twice in a parameter description block", value.pos)
        self.properties_set.add(name)
        if name == 'names':
            for name_value in value:
                num = name_value.num.reduce_constant().value
                desc = name_value.desc
                if not isinstance(desc, expression.String):
                    raise generic.ScriptError("setting name description must be a string", desc.pos)
                self.val_names.append((num, desc))
            return
        value = value.reduce(unknown_id_fatal = False)
        if name == 'type':
            if not isinstance(value, expression.Identifier) or (value.value != 'int' and value.value != 'bool'):
                raise generic.ScriptError("setting-type must be either 'int' or 'bool'", value.pos)
            self.type = value.value
        elif name == 'name':
            if not isinstance(value, expression.String):
                raise generic.ScriptError("setting-name must be a string", value.pos)
            self.name_string = value
        elif name == 'desc':
            if not isinstance(value, expression.String):
                raise generic.ScriptError("setting-description must be a string", value.pos)
            self.desc_string = value
        elif name == 'bit':
            if self.type != 'bool':
                raise generic.ScriptError("setting-bit is only valid for 'bool' settings", value.pos)
            self.bit_num = value.reduce_constant()
        elif name == 'min_value':
            if self.type != 'int':
                raise generic.ScriptError("setting-min_value is only valid for 'int' settings", value.pos)
            self.min_val = value.reduce_constant()
        elif name == 'max_value':
            if self.type != 'int':
                raise generic.ScriptError("setting-max_value is only valid for 'int' settings", value.pos)
            self.max_val = value.reduce_constant()
        elif name == 'def_value':
            self.def_val = value.reduce_constant()
            if self.type == 'bool' and self.def_val.value != 0 and self.def_val.value != 1:
                raise generic.ScriptError("setting-def_value must be either 0 or 1 for 'bool' settings", value.pos)
        else:
            raise generic.ScriptError("Unknown setting-property " + name, value.pos)

class ParameterDescription(object):
    def __init__(self, setting_list, num = None, pos = None):
        self.setting_list = setting_list
        self.num = num
        self.pos = pos

    def pre_process(self, num):
        if self.num is None: self.num = num
        for setting in self.setting_list:
            setting.pre_process()
        for setting in self.setting_list:
            if setting.type == 'int':
                if len(self.setting_list) > 1:
                    raise generic.ScriptError("When packing multiple settings in one parameter only bool settings are allowed", self.pos)
                global_constants.settings[setting.name.value] = {'num': self.num.value, 'size': 4}
            else:
                bit = 0 if setting.bit_num is None else setting.bit_num.value
                global_constants.misc_grf_bits[setting.name.value] = {'param': self.num.value, 'bit': bit};
