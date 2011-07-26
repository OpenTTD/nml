from nml import generic, expression, global_constants
from nml.actions import base_action, action0, action2, action2var, action3_callbacks, action6, actionD
from nml.ast import switch_range

class Action3(base_action.BaseAction):
    """
    Class representing a single Action3.

    @ivar feature: Action3 feature byte.
    @type feature: C{int}

    @ivar id: Item ID of the item that this action3 represents.
    @type id: C{int}

    @ivar cid_mappings: List of mappings that map cargo IDs to Action2s.
    @type cid_mappings: C{list} of C{tuple}: (C{int}, L{SpriteGroupRef} before prepare_output, C{int} afterwards)

    @ivar def_cid: Default Action2 to use if no cargo ID matches.
    @type def_cid: C{None} or L{SpriteGroupRef} before prepare_output, C{int} afterwards

    @ivar references: All Action2s that are referenced by this Action3.
    @type references: C{list} of L{Action2Reference}
    """
    def __init__(self, feature, id):
        self.feature = feature
        self.id = id
        self.cid_mappings = []
        self.def_cid = None
        self.references = []

    def prepare_output(self):
        action2.free_references(self)
        self.cid_mappings = [(cargo, cid.get_action2_id()) for cargo, cid in self.cid_mappings]
        self.def_cid = 0 if self.def_cid is None else self.def_cid.get_action2_id()

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
        for cargo, cid in self.cid_mappings:
            file.print_bytex(cargo)
            file.print_wordx(cid)
            file.newline()
        file.print_wordx(self.def_cid)
        file.newline()
        file.end_sprite()

    def skip_action9(self):
        return False

# Make sure all action2s created here get a unique name
action2_id = 0

def create_intermediate_varaction2(feature, var_num, and_mask, mapping, default):
    """
    Create a varaction2 that maps callback numbers to various sprite groups

    @param feature: Feature of the varaction2
    @type feature: C{int}

    @param var_num: Number of the variable to evaluate
    @type var_num: C{int}

    @param and_mask: And-mask to use for the variable
    @type and_mask: C{int}

    @param mapping: Mapping of various values to sprite groups
    @type mapping: C{dict} that maps C{int} to L{SpriteGroupRef}

    @param default: Default sprite group if no value matches
    @type default: L{SpriteGroupRef}

    @return: A tuple containing the action list and a reference to the created action2
    @rtype: C{tuple} of (C{list} of L{BaseAction}, L{SpriteGroupRef})
    """
    global action2_id
    varact2parser = action2var.Varaction2Parser(feature)
    varact2parser.parse_expr(expression.Variable(expression.ConstantNumeric(var_num), mask = expression.ConstantNumeric(and_mask)))

    action_list = varact2parser.extra_actions
    extra_act6 = action6.Action6()
    for mod in varact2parser.mods:
        extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
    if len(extra_act6.modifications) > 0: action_list.append(extra_act6)

    name = expression.Identifier("@action3_%d" % action2_id)
    action2_id += 1
    varaction2 = action2var.Action2Var(feature, name.value, 0x89)
    varaction2.var_list = varact2parser.var_list
    for value in sorted(mapping):
        varaction2.ranges.append(action2var.Varaction2Range(expression.ConstantNumeric(value), expression.ConstantNumeric(value), mapping[value], mapping[value].name.value))
        action2.add_ref(mapping[value], varaction2)
    varaction2.default_result = default
    action2.add_ref(default, varaction2)
    varaction2.default_comment = default.name.value

    return_ref = expression.SpriteGroupRef(name, [], None, varaction2)
    action_list.append(varaction2)
    return (action_list, return_ref)

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

def parse_graphics_block(graphics_list, default_graphics, feature, id, is_livery_override = False):
    action6.free_parameters.save()
    prepend_action_list = []
    action_list = []
    act6 = action6.Action6()
    act3 = create_action3(feature, id, action_list, act6, is_livery_override)

    cargo_gfx = {}
    seen_callbacks = set()
    callbacks = []
    livery_override = None # Used for rotor graphics

    for graphics in graphics_list:
        cargo_id = graphics.cargo_id
        if isinstance(cargo_id, expression.Identifier):
            cb_name = cargo_id.value
            # Temporary for backwads compatibility
            if cb_name in cargo_conversion_table:
                generic.print_warning("Pseudo-cargo type '%s' is deprecated, please use '%s' instead." % (cb_name, cargo_conversion_table[cb_name]), cargo_id.pos)
                cb_name = cargo_conversion_table[cb_name]
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
                        cargo_gfx[info['num']] = graphics.spritegroup_ref
                    elif info['type'] == 'cb':
                        callbacks.append( (info, graphics.spritegroup_ref) )
                    elif info['type'] == 'override':
                        assert livery_override is None
                        livery_override = graphics.spritegroup_ref
                    else:
                        assert False
                continue

        # Not a callback, so it must be a 'normal' cargo (vehicles/stations only)
        cargo_id = cargo_id.reduce_constant(global_constants.const_list)
        # Raise the error only now, to let the 'unknown identifier' take precedence
        if feature >= 5: raise generic.ScriptError("Associating graphics with a specific cargo is possible only for vehicles and stations.", cargo_id.pos)
        if cargo_id.value in cargo_gfx:
             raise generic.ScriptError("Graphics for cargo %d are defined multiple times." % cargo_id.value, cargo_id.pos)
        cargo_gfx[cargo_id.value] = graphics.spritegroup_ref

    if default_graphics is not None:
        if 'default' not in action3_callbacks.callbacks[feature]:
            raise generic.ScriptError("Default graphics may not be defined for this feature (0x%02X)." % feature, default_graphics.pos)
        if None in cargo_gfx:
            raise generic.ScriptError("Default graphics are defined twice.", default_graphics.pos)
        cargo_gfx[None] = default_graphics

    if len(callbacks) != 0:
        cb_flags = 0
        # Determine the default value
        if None in cargo_gfx:
            default_val = cargo_gfx[None]
        else:
            default_val = expression.SpriteGroupRef(expression.Identifier('CB_FAILED', None), [], None)

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

            # See action3_callbacks for info on possible values
            purchase = cb_info['purchase'] if 'purchase' in cb_info else 0
            if isinstance(purchase, str):
                # Not in purchase list, if separate purchase CB is set
                purchase = 0 if purchase in seen_callbacks else 1
            # Explicit purchase CBs will need a purchase cargo, even if not needed for graphics
            if purchase == 2 and 0xFF not in cargo_gfx:
                cargo_gfx[0xFF] = default_val

            num = cb_info['num']
            if num == 0x36:
                if purchase != 2: cb36_mapping[cb_info['var10']] = gfx
                if purchase != 0: cb36_buy_mapping[cb_info['var10']] = gfx
            elif feature == 0x0A and num == 0x00:
                # Industry production CB
                assert purchase == 0
                prod_cb_mapping[cb_info['var18']] = gfx
            else:
                if purchase != 2: cb_mapping[num] = gfx
                if purchase != 0: cb_buy_mapping[num] = gfx

        if cb_flags != 0:
            prepend_action_list.extend(action0.get_callback_flags_actions(feature, id, cb_flags))

        # Handle CB 36
        if len(cb36_mapping) != 0:
            actions, cb36_ref = create_intermediate_varaction2(feature, 0x10, 0xFF, cb36_mapping, default_val)
            prepend_action_list.extend(actions)
            cb_mapping[0x36] = cb36_ref
        if len(cb36_buy_mapping) != 0:
            actions, cb36_ref = create_intermediate_varaction2(feature, 0x10, 0xFF, cb36_buy_mapping, default_val)
            prepend_action_list.extend(actions)
            cb_buy_mapping[0x36] = cb36_ref
        if len(prod_cb_mapping) != 0:
            # If only one of the production CBs is enabled, just write it as CB 0
            # The other one won't be called anyway, as it requires a CB flag bit
            if len(prod_cb_mapping) == 1:
                cb_mapping[0x00] = prod_cb_mapping.values().pop()
            else:
                actions, cb_ref = create_intermediate_varaction2(feature, 0x18, 0xFF, prod_cb_mapping, default_val)
                prepend_action_list.extend(actions)
                cb_mapping[0x00] = cb_ref

        for cargo in sorted(cargo_gfx):
            mapping = cb_buy_mapping if cargo == 0xFF else cb_mapping
            if len(mapping) == 0:
                # No callbacks here, so move along
                continue
            if feature <= 0x04:
                # For vehicles and stations, there are cargo-specific gfx
                mapping = mapping.copy()
                mapping[0x00] = cargo_gfx[cargo]
            actions, cb_ref = create_intermediate_varaction2(feature, 0x0C, 0xFFFF, mapping, default_val)
            prepend_action_list.extend(actions)
            cargo_gfx[cargo] = cb_ref

    # Make sure to sort to make the order well-defined
    for cargo_id in sorted(cargo_gfx):
        action2.add_ref(cargo_gfx[cargo_id], act3)
        if cargo_id is None:
            act3.def_cid = cargo_gfx[None]
        else:
            act3.cid_mappings.append( (cargo_id, cargo_gfx[cargo_id]) )

    if livery_override is not None:
        act6livery = action6.Action6()
        # Add any extra actions before the main action3 (TTDP requirement)
        act3livery = create_action3(feature, id, action_list, act6livery, True)
        act3livery.def_cid = livery_override
        action2.add_ref(livery_override, act3livery)

    if len(act6.modifications) > 0: action_list.append(act6)
    action_list.append(act3)
    if livery_override is not None:
        if len(act6livery.modifications) > 0: action_list.append(act6livery)
        action_list.append(act3livery)
    action6.free_parameters.restore()

    return prepend_action_list + action_list

# Temporary conversion table
cargo_conversion_table = {
    'GUI'             : 'gui',
    'TRACKOVERLAY'    : 'track_overlay',
    'UNDERLAY'        : 'underlay',
    'TUNNELS'         : 'tunnels',
    'CATENARY_WIRE'   : 'caternary_wire',
    'CATENARY_PYLONS' : 'caternary_pylons',
    'BRIDGE_SURFACES' : 'bridge_surfaces',
    'LEVEL_CROSSINGS' : 'level_crossings',
    'DEPOTS'          : 'depots',
    'FENCES'          : 'fences',
    'PURCHASE_LIST'   : 'purchase'
}

