from nml.actions.action0properties import Action0Property, properties
from nml import generic, expression
from nml.actions import base_action, action4, action6, actionD

class Action0(base_action.BaseAction):
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.prop_list = []
        self.num_ids = None

    def prepare_output(self):
        if self.num_ids is None: self.num_ids = 1

    def write(self, file):
        size = 7
        for prop in self.prop_list: size += prop.get_size()
        file.start_sprite(size)
        file.print_bytex(0)
        file.print_bytex(self.feature)
        file.print_byte(len(self.prop_list))
        file.print_bytex(self.num_ids)
        file.print_bytex(0xFF)
        file.print_wordx(self.id)
        file.newline()
        for prop in self.prop_list:
            prop.write(file)
        file.end_sprite()

first_free_id = [116, 88, 11, 41] + 0x0E * [0]

def get_free_id(feature):
    global first_free_id
    first_free_id[feature] += 1
    return first_free_id[feature] - 1


def parse_property(feature, name, value, id, unit):
    global properties
    prop = None
    action_list = []
    action_list_append = []
    mods = []

    #Validate feature
    assert feature in range (0, len(properties)) #guaranteed by item
    if properties[feature] is None:
        raise generic.ScriptError("Setting properties for feature %s is not possible, no properties are defined." % generic.to_hex(feature, 2), name.pos)

    if isinstance(name, expression.Identifier):
        if not name.value in properties[feature]: raise generic.ScriptError("Unknown property name: " + name.value, name.pos)
        prop = properties[feature][name.value]
    elif isinstance(name, expression.ConstantNumeric):
        for p in properties[feature]:
            pdata = properties[feature][p]
            if 'num' not in pdata or pdata['num'] != name.value: continue
            prop = pdata
        if prop is None: raise generic.ScriptError("Unknown property number: " + str(name), name.pos)
    else: assert False

    if unit is None or unit.type != 'nfo':
        mul = 1
        if 'unit_conversion' in prop: mul = prop['unit_conversion']
        if unit is not None:
            if not 'unit_type' in prop or unit.type != prop['unit_type']:
                raise generic.ScriptError("Invalid unit for property: " + str(name), name.pos)
            mul = mul / unit.convert
        if mul != 1 or isinstance(value, expression.ConstantFloat): #always round floats
            if not isinstance(value, (expression.ConstantNumeric, expression.ConstantFloat)):
                raise generic.ScriptError("Unit conversion specified for property, but no constant value found", value.pos)
            value = expression.ConstantNumeric(int(value.value * mul + 0.5), value.pos)

    if 'custom_function' in prop:
        props = prop['custom_function'](value)
    elif 'string_literal' in prop:
        if not isinstance(value, expression.StringLiteral): raise generic.ScriptError("Value for property %d must be a string literal" % prop['num'], value.pos)
        if len(value.value) != prop['string_literal']:
            raise generic.ScriptError("Value for property %d must be of length %d" % (prop['num'], prop['string_literal']), value.pos)
        props = [Action0Property(prop['num'], value, prop['size'])]
    else:
        if isinstance(value, expression.ConstantNumeric):
            pass
        elif isinstance(value, expression.Parameter) and isinstance(value.num, expression.ConstantNumeric):
            mods.append((value.num.value, prop['size'], 1))
            value = expression.ConstantNumeric(0)
        elif isinstance(value, expression.String):
            if not 'string' in prop: raise generic.ScriptError("String used as value for non-string property: " + str(prop['num']), value.pos)
            string_range = prop['string']
            stringid, prepend, string_actions = action4.get_string_action4s(feature, string_range, value, id)
            value = expression.ConstantNumeric(stringid)
            if prepend:
                action_list.extend(string_actions)
            else:
                action_list_append.extend(string_actions)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(value)
            mods.append((tmp_param, prop['size'], 1))
            action_list.extend(tmp_param_actions)
            value = expression.ConstantNumeric(0)
        if prop['num'] != -1:
            props = [Action0Property(prop['num'], value, prop['size'])]
        else:
            props = []

    if 'append_function' in prop:
        props.extend(prop['append_function'](value))

    return (props, action_list, mods, action_list_append)

def parse_property_block(prop_list, feature, id):
    action6.free_parameters.save()
    action_list = []
    action_list_append = []
    act6 = action6.Action6()
    if isinstance(id, expression.ConstantNumeric):
        action0 = Action0(feature, id.value)
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(id)
        act6.modify_bytes(tmp_param, 2, 5)
        action_list.extend(tmp_param_actions)
        action0 = Action0(feature, 0)

    offset = 7
    for prop in prop_list:
        properties, extra_actions, mods, extra_append_actions = parse_property(feature, prop.name, prop.value, id.value, prop.unit)
        action_list.extend(extra_actions)
        action_list_append.extend(extra_append_actions)
        for mod in mods:
            act6.modify_bytes(mod[0], mod[1], mod[2] + offset)
        for p in properties:
            offset += p.get_size()
        action0.prop_list.extend(properties)

    if len(act6.modifications) > 0: action_list.append(act6)
    if len(action0.prop_list) != 0:
        action_list.append(action0)

    action_list.extend(action_list_append)

    action6.free_parameters.restore()
    return action_list

class IDListProp(object):
    def __init__(self, prop_num, id_list):
        self.prop_num = prop_num
        self.id_list = id_list

    def write(self, file):
        file.print_bytex(self.prop_num)
        for i, id_val in enumerate(self.id_list):
            if i > 0 and i % 5 == 0: file.newline()
            file.print_string(id_val.value, False, True)
        file.newline()

    def get_size(self):
        return len(self.id_list) * 4 + 1

def get_cargolist_action(cargo_list):
    action0 = Action0(0x08, 0)
    action0.prop_list.append(IDListProp(0x09, cargo_list))
    action0.num_ids = len(cargo_list)
    return [action0]

def get_railtypelist_action(railtype_list):
    action0 = Action0(0x08, 0)
    action0.prop_list.append(IDListProp(0x12, railtype_list))
    action0.num_ids = len(railtype_list)
    return [action0]

class ByteListProp(object):
    def __init__(self, prop_num, data):
        self.prop_num = prop_num
        self.data = data

    def write(self, file):
        file.print_bytex(self.prop_num)
        file.newline()
        for i, data_val in enumerate(self.data):
            if i > 0 and i % 8 == 0: file.newline()
            file.print_bytex(ord(data_val))
        file.newline()

    def get_size(self):
        return len(self.data) + 1

def get_snowlinetable_action(snowline_table):
    assert(len(snowline_table) == 12*32)
    action0 = Action0(0x08, 0)
    action0.prop_list.append(ByteListProp(0x10, snowline_table))
    action0.num_ids = 1
    return [action0]

def get_basecost_action(basecost):
    action6.free_parameters.save()
    action_list = []
    tmp_param_map = {} #Cache for tmp parameters

    #We want to avoid writing lots of action0s if possible
    i = 0
    while i < len(basecost.costs):
        cost = basecost.costs[i]
        act6 = action6.Action6()

        index = 0xFF #placeholder, overwritten by either the real value or action6
        if isinstance(cost.name, expression.ConstantNumeric):
            index = cost.name.value
        elif isinstance(cost.name, expression.Parameter) and isinstance(cost.name.num, expression.ConstantNumeric):
            act6.modify_bytes(cost.name.num.value, 2, 5)
        else:
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(cost.name)
            act6.modify_bytes(tmp_param, 2, 5)
            action_list.extend(tmp_param_actions)
        act0 = Action0(0x08, index)

        num_ids = 1 #Number of values that will be written in one go
        values = []
        #try to capture as much values as possible
        while True:
            cost = basecost.costs[i]
            if isinstance(cost.value, expression.ConstantNumeric):
                values.append(cost.value)
            else:
                #Cache lookup, saves some ActionDs
                if cost.value in tmp_param_map:
                    tmp_param, tmp_param_actions = tmp_param_map[cost.value], []
                else:
                    tmp_param, tmp_param_actions = actionD.get_tmp_parameter(cost.value)
                    tmp_param_map[cost.value] = tmp_param
                act6.modify_bytes(tmp_param, 1, 7 + num_ids)
                action_list.extend(tmp_param_actions)
                values.append(expression.ConstantNumeric(0))

            #check if we can append the next to this one (it has to be consecutively numbered)
            if (i + 1) < len(basecost.costs):
                nextcost = basecost.costs[i+1]
                if isinstance(nextcost.name, expression.ConstantNumeric) and nextcost.name.value == index + num_ids:
                    num_ids += 1
                    i += 1
                    #Yes We Can, continue the loop to append this value to the list and try further
                    continue
            # No match, so stop it and write an action0
            break

        act0.prop_list.append(Action0Property(0x08, values, 1))
        act0.num_ids = num_ids
        if len(act6.modifications) > 0: action_list.append(act6)
        action_list.append(act0)
        i += 1
    action6.free_parameters.restore()
    return action_list

class LanguageTranslationTable(object):
    def __init__(self, num, name_list, extra_names):
        self.num = num
        self.mappings = []
        for name, idx in name_list.iteritems():
            self.mappings.append( (idx, name) )
            if name in extra_names:
                for extra_name in extra_names[name]:
                    self.mappings.append( (idx, extra_name) )

    def write(self, file):
        file.print_bytex(self.num)
        for mapping in self.mappings:
            file.print_bytex(mapping[0])
            file.print_string(mapping[1])
        file.print_bytex(0)
        file.newline()

    def get_size(self):
        size = 2
        for mapping in self.mappings:
            size += 2 + len(mapping[1])
        return size

def get_language_translation_tables(lang):
    action0 = Action0(0x08, lang.langid)
    if lang.genders is not None:
        action0.prop_list.append(LanguageTranslationTable(0x13, lang.genders, lang.gender_map))
    if lang.cases is not None:
        action0.prop_list.append(LanguageTranslationTable(0x14, lang.cases, lang.case_map))
    if lang.plural is not None:
        action0.prop_list.append(Action0Property(0x15, expression.ConstantNumeric(lang.plural), 1))
    if len(action0.prop_list) > 0:
        return [action0]
    return []
