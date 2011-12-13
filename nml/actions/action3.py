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

from nml import generic, expression, global_constants
from nml.actions import base_action, action0, action2, action2real, action2var, action3_callbacks, action6, actionD

class Action3(base_action.BaseAction):
    """
    Class representing a single Action3.

    @ivar feature: Action3 feature byte.
    @type feature: C{int}

    @ivar id: Item ID of the item that this action3 represents.
    @type id: C{int}

    @ivar cid_mappings: List of mappings that map cargo IDs to Action2s.
    @type cid_mappings: C{list} of C{tuple}: (C{int}, L{Expression} before prepare_output, C{int} afterwards, C{str})

    @ivar def_cid: Default Action2 to use if no cargo ID matches.
    @type def_cid: C{None} or L{SpriteGroupRef} before prepare_output, C{int} afterwards

    @ivar references: All Action2s that are referenced by this Action3.
    @type references: C{list} of L{Action2Reference}
    """
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.cid_mappings = []
        self.references = []

    def prepare_output(self):
        action2.free_references(self)
        map_cid = lambda cid: cid.get_action2_id(self.feature) if isinstance(cid, expression.SpriteGroupRef) else cid.value | 0x8000
        self.cid_mappings = [(cargo, map_cid(cid), comment) for cargo, cid, comment in self.cid_mappings]
        if self.def_cid is None:
            self.def_cid = 0
        else:
            self.def_cid = map_cid(self.def_cid)

    def write(self, file):
        size = 7 + 3 * len(self.cid_mappings)
        if self.feature <= 3: size += 2 # Vehicles use extended byte
        file.start_sprite(size)
        file.print_bytex(3)
        file.print_bytex(self.feature)
        file.print_bytex(1 if not self.is_livery_override else 0x81) # a single id
        file.print_varx(self.id, 3 if self.feature <= 3 else 1)
        file.print_byte(len(self.cid_mappings))
        file.newline()
        for cargo, cid, comment in self.cid_mappings:
            file.print_bytex(cargo)
            file.print_wordx(cid)
            file.newline(comment)
        file.print_wordx(self.def_cid)
        file.newline(self.default_comment)
        file.end_sprite()

    def skip_action9(self):
        return False

# Make sure all action2s created here get a unique name
action2_id = 0

def create_intermediate_varaction2(feature, varact2parser, mapping, default):
    """
    Create a varaction2 based on a parsed expression and a value mapping

    @param feature: Feature of the varaction2
    @type feature: C{int}

    @param varact2parser: Parser containing a parsed expression
    @type varact2parser: L{Varaction2Parser}

    @param mapping: Mapping of various values to sprite groups / return values, with a possible extra function to apply to the return value
    @type mapping: C{dict} that maps C{int} to C{tuple} of (L{SpriteGroupRef}, C{function}, or C{None})

    @param default: Default sprite group if no value matches
    @type default: L{SpriteGroupRef}

    @return: A tuple containing the action list and a reference to the created action2
    @rtype: C{tuple} of (C{list} of L{BaseAction}, L{SpriteGroupRef})
    """
    global action2_id

    action_list = varact2parser.extra_actions
    act6 = action6.Action6()
    for mod in varact2parser.mods:
        act6.modify_bytes(mod.param, mod.size, mod.offset + 4)

    name = expression.Identifier("@action3_%d" % action2_id)
    action2_id += 1
    varaction2 = action2var.Action2Var(feature, name.value, 0x89)
    varaction2.var_list = varact2parser.var_list
    offset = 5 + varact2parser.var_list_size
    for proc in varact2parser.proc_call_list:
        action2.add_ref(proc, varaction2, True)

    for switch_value in sorted(mapping):
        return_value, ret_value_function = mapping[switch_value]
        if ret_value_function is None:
            result, comment = action2var.parse_result(return_value, action_list, act6, offset, varaction2, None, 0x89)
        else:
            if isinstance(return_value, expression.SpriteGroupRef):
                # We need to execute the callback via a procedure call
                # then return CB_FAILED if the CB failed,
                # or the CB result (with ret_value_function applied) if successful
                if return_value.name.value == 'CB_FAILED':
                    result, comment = action2var.parse_result(return_value, action_list, act6, offset, varaction2, None, 0x89)
                else:
                    extra_actions, result, comment = create_proc_call_varaction2(feature, return_value, ret_value_function)
                    action_list.extend(extra_actions)
            else:
                return_value = ret_value_function(return_value).reduce()
                result, comment = action2var.parse_result(return_value, action_list, act6, offset, varaction2, None, 0x89)

        varaction2.ranges.append(action2var.VarAction2Range(expression.ConstantNumeric(switch_value), expression.ConstantNumeric(switch_value), result, comment))
        offset += 10
    result, comment = action2var.parse_result(default, action_list, act6, offset, varaction2, None, 0x89)
    varaction2.default_result = result
    varaction2.default_comment = comment

    return_ref = expression.SpriteGroupRef(name, [], None, varaction2)
    if len(act6.modifications) > 0: action_list.append(act6)
    action_list.append(varaction2)
    return (action_list, return_ref)

def create_proc_call_varaction2(feature, proc, ret_value_function):
    """
    Create a varaction2 that executes a procedure call and applies a function on the result

    @param feature: Feature of the varaction2
    @type feature: C{int}

    @param proc: Procedure to execute
    @type proc: L{SpriteGroupRef}

    @param ret_value_function: Function to apply on the result (L{Expression} -> L{Expression})
    @type ret_value_function: C{function}

    @return: A list of extra actions, reference to the created action2 and a comment to add
    @rtype: C{tuple} of (C{list} of L{BaseAction}, L{SpriteGroupRef}, C{str})
    """
    varact2parser = action2var.Varaction2Parser(feature)
    varact2parser.parse_proc_call(proc)

    mapping = {0xFFFF: (expression.SpriteGroupRef(expression.Identifier('CB_FAILED'), [], None), None)}
    default = ret_value_function(expression.Variable(expression.ConstantNumeric(0x1C)))
    action_list, result = create_intermediate_varaction2(feature, varact2parser, mapping, default)
    comment = result.name.value + ';'
    return (action_list, result, comment)

def create_cb_choice_varaction2(feature, var_num, and_mask, mapping, default):
    """
    Create a varaction2 that maps callback numbers to various sprite groups

    @param feature: Feature of the varaction2
    @type feature: C{int}

    @param var_num: Number of the variable to evaluate
    @type var_num: C{int}

    @param and_mask: And-mask to use for the variable
    @type and_mask: C{int}

    @param mapping: Mapping of various values to sprite groups, with a possible extra function to apply to the return value
    @type mapping: C{dict} that maps C{int} to C{tuple} of (L{SpriteGroupRef}, C{function}, or C{None})

    @param default: Default sprite group if no value matches
    @type default: L{SpriteGroupRef}

    @return: A tuple containing the action list and a reference to the created action2
    @rtype: C{tuple} of (C{list} of L{BaseAction}, L{SpriteGroupRef})
    """
    varact2parser = action2var.Varaction2Parser(feature)
    varact2parser.parse_expr(expression.Variable(expression.ConstantNumeric(var_num), mask = expression.ConstantNumeric(and_mask)))
    return create_intermediate_varaction2(feature, varact2parser, mapping, default)

def create_action3(feature, id, action_list, act6, is_livery_override):
    if isinstance(id, expression.ConstantNumeric):
        act3 = Action3(feature, id.value)
    else:
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(id)
        # Vehicles use an extended byte
        size = 2 if feature <= 3 else 1
        offset = 4 if feature <= 3 else 3
        act6.modify_bytes(tmp_param, size, offset)
        action_list.extend(tmp_param_actions)
        act3 = Action3(feature, 0)

    act3.is_livery_override = is_livery_override
    return act3

def parse_graphics_block(graphics_block, feature, id, is_livery_override = False):
    action6.free_parameters.save()
    prepend_action_list = action2real.create_spriteset_actions(graphics_block)
    action_list = []
    act6 = action6.Action6()
    act3 = create_action3(feature, id, action_list, act6, is_livery_override)

    cargo_gfx = {}
    seen_callbacks = set()
    callbacks = []
    livery_override = None # Used for rotor graphics

    for graphics in graphics_block.graphics_list:
        cargo_id = graphics.cargo_id
        if isinstance(cargo_id, expression.Identifier):
            cb_name = cargo_id.value
            cb_table = action3_callbacks.callbacks[feature]
            if cb_name in cb_table:
                if cb_name in seen_callbacks:
                    raise generic.ScriptError("Callback '%s' is defined multiple times." % cb_name, cargo_id.pos)
                seen_callbacks.add(cb_name)

                info_list = cb_table[cb_name]
                if not isinstance(info_list, list):
                    info_list = [info_list]

                for info in info_list:
                    if info['type'] == 'cargo':
                        # Not a callback, but an alias for a certain cargo type
                        if info['num'] in cargo_gfx:
                            raise generic.ScriptError("Graphics for '%s' are defined multiple times." % cb_name, cargo_id.pos)
                        cargo_gfx[info['num']] = graphics.result
                    elif info['type'] == 'cb':
                        callbacks.append( (info, graphics.result) )
                    elif info['type'] == 'override':
                        assert livery_override is None
                        livery_override = graphics.result
                    else:
                        assert False
                continue

        # Not a callback, so it must be a 'normal' cargo (vehicles/stations only)
        cargo_id = cargo_id.reduce_constant(global_constants.const_list)
        # Raise the error only now, to let the 'unknown identifier' take precedence
        if feature >= 5: raise generic.ScriptError("Associating graphics with a specific cargo is possible only for vehicles and stations.", cargo_id.pos)
        if cargo_id.value in cargo_gfx:
             raise generic.ScriptError("Graphics for cargo %d are defined multiple times." % cargo_id.value, cargo_id.pos)
        cargo_gfx[cargo_id.value] = graphics.result

    if graphics_block.default_graphics is not None:
        if 'default' not in action3_callbacks.callbacks[feature]:
            raise generic.ScriptError("Default graphics may not be defined for this feature (0x%02X)." % feature, graphics_block.default_graphics.pos)
        if None in cargo_gfx:
            raise generic.ScriptError("Default graphics are defined twice.", graphics_block.default_graphics.pos)
        cargo_gfx[None] = graphics_block.default_graphics

    if len(callbacks) != 0:
        cb_flags = 0
        # Determine the default value
        if None not in cargo_gfx:
            cargo_gfx[None] = expression.SpriteGroupRef(expression.Identifier('CB_FAILED', None), [], None)
        default_val = cargo_gfx[None]

        cb_mapping = {}
        cb_buy_mapping = {}
        # Special case for vehicle cb 36, maps var10 values to spritegroups
        cb36_mapping = {}
        cb36_buy_mapping = {}
        # Sspecial case for industry production CB, maps var18 values to spritegroups
        prod_cb_mapping = {}

        for cb_info, gfx in callbacks:
            if 'flag_bit' in cb_info:
                # Set a bit in the CB flags property
                cb_flags |= 1 << cb_info['flag_bit']

            value_function = cb_info.get('value_function', None)
            mapping_val = (gfx, value_function) 

            # See action3_callbacks for info on possible values
            purchase = cb_info.get('purchase', 0)
            if isinstance(purchase, str):
                # Not in purchase list, if separate purchase CB is set
                purchase = 0 if purchase in seen_callbacks else 1
            # Explicit purchase CBs will need a purchase cargo, even if not needed for graphics
            if purchase == 2 and 0xFF not in cargo_gfx:
                cargo_gfx[0xFF] = default_val

            num = cb_info['num']
            if num == 0x36:
                if purchase != 2: cb36_mapping[cb_info['var10']] = mapping_val
                if purchase != 0: cb36_buy_mapping[cb_info['var10']] = mapping_val
            elif feature == 0x0A and num == 0x00:
                # Industry production CB
                assert purchase == 0
                prod_cb_mapping[cb_info['var18']] = mapping_val
            else:
                if purchase != 2: cb_mapping[num] = mapping_val
                if purchase != 0: cb_buy_mapping[num] = mapping_val

        if cb_flags != 0:
            prepend_action_list.extend(action0.get_callback_flags_actions(feature, id, cb_flags))

        # Handle CB 36
        if len(cb36_mapping) != 0:
            actions, cb36_ref = create_cb_choice_varaction2(feature, 0x10, 0xFF, cb36_mapping, default_val)
            prepend_action_list.extend(actions)
            cb_mapping[0x36] = (cb36_ref, None)
        if len(cb36_buy_mapping) != 0:
            actions, cb36_ref = create_cb_choice_varaction2(feature, 0x10, 0xFF, cb36_buy_mapping, default_val)
            prepend_action_list.extend(actions)
            cb_buy_mapping[0x36] = (cb36_ref, None)
        if len(prod_cb_mapping) != 0:
            actions, cb_ref = create_cb_choice_varaction2(feature, 0x18, 0xFF, prod_cb_mapping, default_val)
            prepend_action_list.extend(actions)
            cb_mapping[0x00] = (cb_ref, None)

        for cargo in sorted(cargo_gfx):
            mapping = cb_buy_mapping if cargo == 0xFF else cb_mapping
            if len(mapping) == 0:
                # No callbacks here, so move along
                continue
            if cargo_gfx[cargo] != default_val:
                # There are cargo-specific graphics, be sure to handle those
                # Unhandled callbacks should chain to the default, though
                mapping = mapping.copy()
                mapping[0x00] = (cargo_gfx[cargo], None)
            actions, cb_ref = create_cb_choice_varaction2(feature, 0x0C, 0xFFFF, mapping, default_val)
            prepend_action_list.extend(actions)
            cargo_gfx[cargo] = cb_ref

    # Make sure to sort to make the order well-defined
    offset = 7 if feature <= 3 else 5
    for cargo_id in sorted(cargo_gfx):
        if cargo_id is None: continue
        result, comment = action2var.parse_result(cargo_gfx[cargo_id], action_list, act6, offset + 1, act3, None, 0x89)
        act3.cid_mappings.append( (cargo_id, result, comment) )
        offset += 3
    if None in cargo_gfx:
        result, comment = action2var.parse_result(cargo_gfx[None], action_list, act6, offset, act3, None, 0x89)
        act3.def_cid = result
        act3.default_comment = comment
    else:
        act3.def_cid = None
        act3.default_comment = ''

    if livery_override is not None:
        act6livery = action6.Action6()
        # Add any extra actions before the main action3 (TTDP requirement)
        act3livery = create_action3(feature, id, action_list, act6livery, True)
        offset = 7 if feature <= 3 else 5
        result, comment = action2var.parse_result(livery_override, action_list, act6livery, offset, act3livery, None, 0x89)
        act3livery.def_cid = result
        act3livery.default_comment = comment

    if len(act6.modifications) > 0: action_list.append(act6)
    action_list.append(act3)
    if livery_override is not None:
        if len(act6livery.modifications) > 0: action_list.append(act6livery)
        action_list.append(act3livery)
    action6.free_parameters.restore()

    return prepend_action_list + action_list

