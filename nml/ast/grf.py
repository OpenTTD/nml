__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml import expression, generic, grfstrings, global_constants
from nml.actions import action8, action14
from nml.ast import base_statement

palette_node = None
blitter_node = None

def set_palette_used(pal):
    """
    Set the used palette in the action 14 node, if applicable

    @param pal: Palette to use
    @type pal: C{str} of length 1
    """
    if palette_node:
        palette_node.pal = pal

def set_preferred_blitter(blitter):
    """
    Set the preferred blitter in the action14 node, if applicable
    
    @param blitter: The blitter to set
    @type blitter: C{str} of length 1
    """
    if blitter_node:
        blitter_node.blitter = blitter

class GRF(base_statement.BaseStatement):
    """
    AST Node for a grf block, that supplies (static) information about the GRF
    This is equivalent to actions 8 and 14

    @ivar name: Name of the GRF (short)
    @type name: L{Expression}, should be L{String} else user error

    @ivar desc: Description of the GRF (longer)
    @type name: L{Expression}, should be L{String} else user error

    @ivar grfid: Globally unique identifier of the GRF
    @type grfid: L{Expression}, should be L{StringLiteral} of 4 bytes else user error

    @ivar version: Version of this GRF
    @type version: L{Expression}

    @ivar min_compatible_version: Minimum (older) version of the same GRF that it is compatible with
    @type min_compatible_version: L{Expression}

    @ivar params: List of user-configurable GRF parameters
    @type params: C{list} of L{ParameterDescription}
    """
    def __init__(self, alist, pos):
        base_statement.BaseStatement.__init__(self, "grf-block", pos, False, False)
        self.name = None
        self.desc = None
        self.url = None
        self.grfid = None
        self.version = None
        self.min_compatible_version = None
        self.params = []
        generic.OnlyOnce.enforce(self, "GRF-block")
        for assignment in alist:
            if isinstance(assignment, ParameterDescription):
                self.params.append(assignment)
            elif assignment.name.value == "name": self.name = assignment.value
            elif assignment.name.value == "desc": self.desc = assignment.value
            elif assignment.name.value == "url": self.url = assignment.value
            elif assignment.name.value == "grfid": self.grfid = assignment.value
            elif assignment.name.value == "version": self.version = assignment.value
            elif assignment.name.value == "min_compatible_version": self.min_compatible_version = assignment.value
            else: raise generic.ScriptError("Unknown item in GRF-block: " + str(assignment.name), assignment.name.pos)

    def pre_process(self):
        if None in (self.name, self.desc, self.grfid, self.version, self.min_compatible_version):
            raise generic.ScriptError("A GRF-block requires the 'name', 'desc', 'grfid', 'version' and 'min_compatible_version' properties to be set.", self.pos)

        self.grfid = self.grfid.reduce()
        global_constants.constant_numbers['GRFID'] = expression.parse_string_to_dword(self.grfid)
        self.name = self.name.reduce()
        if not isinstance(self.name, expression.String):
            raise generic.ScriptError("GRF-name must be a string", self.name.pos)
        grfstrings.validate_string(self.name)
        self.desc = self.desc.reduce()
        if not isinstance(self.desc, expression.String):
            raise generic.ScriptError("GRF-description must be a string", self.desc.pos)
        grfstrings.validate_string(self.desc)
        if self.url is not None:
            self.url = self.url.reduce()
            if not isinstance(self.url, expression.String):
                raise generic.ScriptError("URL must be a string", self.url.pos)
            grfstrings.validate_string(self.url)
        self.version = self.version.reduce_constant()
        self.min_compatible_version = self.min_compatible_version.reduce_constant()
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
        if self.url is not None:
            print (2+indentation)*' ' + 'URL:'
            self.url.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Version:'
        self.version.debug_print(indentation + 4)
        print (2+indentation)*' ' + 'Minimal compatible version:'
        self.min_compatible_version.debug_print(indentation + 4)

    def get_action_list(self):
        global palette_node, blitter_node
        palette_node = action14.UsedPaletteNode("A")
        blitter_node = action14.BlitterNode("8")
        action14_root = action14.BranchNode("INFO")
        action14.grf_name_desc_actions(action14_root, self.name, self.desc, self.url, self.version, self.min_compatible_version)
        action14.param_desc_actions(action14_root, self.params)
        action14_root.subnodes.append(palette_node)
        action14_root.subnodes.append(blitter_node)
        return action14.get_actions(action14_root) + [action8.Action8(self.grfid, self.name, self.desc)]

    def __str__(self):
        ret = 'grf {\n'
        ret += '\tgrfid: %s;\n' % str(self.grfid)
        ret += '\tname: %s;\n' % str(self.name)
        ret += '\tdesc: %s;\n' % str(self.desc)
        if self.url is not None:
            ret += '\turl: %s;\n' % str(self.url)
        ret += '\tversion: %s;\n' % str(self.version)
        ret += '\tmin_compatible_version: %s;\n' % str(self.min_compatible_version)
        for param in self.params:
            ret += str(param)
        ret += '}\n'
        return ret

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

    def __str__(self):
        ret = "\t\t%s {\n" % str(self.name)
        for val in self.value_list:
            if val.name.value == 'names':
                ret += "\t\t\tnames: {\n"
                for name in val.value.values:
                    ret += "\t\t\t\t%s: %s;\n" % (name.name, name.value)
                ret += "\t\t\t};\n"
            else:
                ret += "\t\t\t%s: %s;\n" % (val.name, val.value)
        ret += "\t\t}\n"
        return ret

    def set_property(self, name, value):
        """
        Set a single parameter property

        @param name: Name of the property to be set
        @type name: C{basestring}

        @param value: Value of the property (note: may be an array)
        @type value: L{Expression}
        """
        if name in self.properties_set:
            raise generic.ScriptError("You cannot set the same property twice in a parameter description block", value.pos)
        self.properties_set.add(name)
        if name == 'names':
            for name_value in value.values:
                num = name_value.name.reduce_constant().value
                desc = name_value.value
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

    def __str__(self):
        ret = "\tparam"
        if self.num:
            ret += " " + str(self.num)
        ret += " {\n"
        for setting in self.setting_list:
            ret += str(setting)
        ret += "\t}\n"
        return ret

    def pre_process(self, num):
        if self.num is None: self.num = num
        self.num = self.num.reduce_constant()
        for setting in self.setting_list:
            setting.pre_process()
        for setting in self.setting_list:
            if setting.type == 'int':
                if len(self.setting_list) > 1:
                    raise generic.ScriptError("When packing multiple settings in one parameter only bool settings are allowed", self.pos)
                global_constants.settings[setting.name.value] = {'num': self.num.value, 'size': 4}
            else:
                bit = 0 if setting.bit_num is None else setting.bit_num.value
                global_constants.misc_grf_bits[setting.name.value] = {'param': self.num.value, 'bit': bit}
