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

from nml import expression, generic, nmlop
from nml.actions import action0, action1, action2, action2real, action2var, action6, actionD, real_sprite
from nml.ast import general, spriteblock


class Action2Layout(action2.Action2):
    def __init__(self, feature, name, pos, layout, param_registers):
        action2.Action2.__init__(self, feature, name, pos)
        self.layout = layout
        self.param_registers = param_registers

    def resolve_tmp_storage(self):
        for reg in self.param_registers:
            if not self.tmp_locations:
                raise generic.ScriptError(
                    "There are not enough registers available "
                    + "to perform all required computations in switch blocks. "
                    + "Please reduce the complexity of your code.",
                    self.pos,
                )
            location = self.tmp_locations[0]
            self.remove_tmp_location(location, False)
            reg.set_register(location)

    def write(self, file):
        size = self.layout.get_size()
        regs = ["{} : register {:X}".format(reg.name, reg.register) for reg in self.param_registers]
        action2.Action2.write_sprite_start(self, file, size, regs)
        self.layout.write(file)
        file.end_sprite()


class Action2LayoutSpriteType:
    GROUND = 0
    BUILDING = 1
    CHILD = 2


# these keywords are used to identify a ground/building/childsprite
layout_sprite_types = {
    "ground": Action2LayoutSpriteType.GROUND,
    "building": Action2LayoutSpriteType.BUILDING,
    "childsprite": Action2LayoutSpriteType.CHILD,
}


class Action2LayoutSprite:
    def __init__(self, feature, type, pos=None, extra_dicts=None):
        self.feature = feature
        self.type = type
        self.pos = pos
        self.extra_dicts = extra_dicts or []
        self.params = {
            "sprite": {"value": None, "validator": self._validate_sprite},
            "recolour_mode": {"value": 0, "validator": self._validate_recolour_mode},
            "palette": {"value": expression.ConstantNumeric(0), "validator": self._validate_palette},
            "always_draw": {"value": 0, "validator": self._validate_always_draw},
            "xoffset": {"value": expression.ConstantNumeric(0), "validator": self._validate_bounding_box},
            "yoffset": {"value": expression.ConstantNumeric(0), "validator": self._validate_bounding_box},
            "zoffset": {"value": expression.ConstantNumeric(0), "validator": self._validate_bounding_box},
            "xextent": {"value": expression.ConstantNumeric(16), "validator": self._validate_bounding_box},
            "yextent": {"value": expression.ConstantNumeric(16), "validator": self._validate_bounding_box},
            "zextent": {"value": expression.ConstantNumeric(16), "validator": self._validate_bounding_box},
            "hide_sprite": {"value": None, "validator": self._validate_hide_sprite},  # Value not used
        }
        for i in self.params:
            self.params[i]["is_set"] = False
            self.params[i]["register"] = None
        self.sprite_from_action1 = False
        self.palette_from_action1 = False
        self.var10_for_sprite = None
        self.var10_for_palette = None

    def is_advanced_sprite(self):
        if self.feature == 0x04:
            return True
        if self.palette_from_action1:
            return True
        return len(self.get_all_registers()) != 0

    def get_registers_size(self):
        # Number of registers to write
        size = len(self.get_all_registers())
        # Add station specific registers
        if self.feature == 0x04:
            if self.var10_for_sprite:
                size += 1
            if self.var10_for_palette:
                size += 1
        # Add 2 for the flags
        size += 2
        return size

    def write_flags(self, file):
        flags = 0
        if self.get_register("hide_sprite") is not None:
            flags |= 1 << 0
        if self.get_register("sprite") is not None:
            flags |= 1 << 1
        if self.get_register("palette") is not None:
            flags |= 1 << 2
        if self.palette_from_action1:
            flags |= 1 << 3
        # for building sprites: bit 4 => xoffset+yoffset, bit 5 => zoffset (x and y always set totgether)
        # for child sprites: bit 4 => xoffset, bit 5 => yoffset
        if self.type == Action2LayoutSpriteType.BUILDING:
            assert (self.get_register("xoffset") is not None) == (self.get_register("yoffset") is not None)
        if self.get_register("xoffset") is not None:
            flags |= 1 << 4
        nextreg = "zoffset" if self.type == Action2LayoutSpriteType.BUILDING else "yoffset"
        if self.get_register(nextreg) is not None:
            flags |= 1 << 5
        if self.feature == 0x04:
            if self.var10_for_sprite is not None:
                flags |= 1 << 6
            if self.var10_for_palette is not None:
                flags |= 1 << 7
        file.print_wordx(flags)

    def write_register(self, file, name):
        register = self.get_register(name)[0]
        file.print_bytex(register.parameter)

    def write_registers(self, file):
        if self.is_set("hide_sprite"):
            self.write_register(file, "hide_sprite")
        if self.get_register("sprite") is not None:
            self.write_register(file, "sprite")
        if self.get_register("palette") is not None:
            self.write_register(file, "palette")
        if self.get_register("xoffset") is not None:
            self.write_register(file, "xoffset")
        if self.get_register("yoffset") is not None:
            self.write_register(file, "yoffset")
        if self.get_register("zoffset") is not None:
            self.write_register(file, "zoffset")
        if self.feature == 0x04:
            if self.var10_for_sprite is not None:
                file.print_bytex(self.var10_for_sprite)
            if self.var10_for_palette is not None:
                file.print_bytex(self.var10_for_palette)

    def write_sprite_number(self, file):
        num = self.get_sprite_number()
        if isinstance(num, expression.ConstantNumeric):
            num.write(file, 4)
        else:
            file.print_dwordx(0)

    def get_sprite_number(self):
        # Layout of sprite number
        # bit  0 - 13: Sprite number
        # bit 14 - 15: Recolour mode (normal/transparent/remap)
        # bit 16 - 29: Palette sprite number
        # bit 30: Always draw sprite, even in transparent mode
        # bit 31: This is a custom sprite (from action1), not a TTD sprite
        if not self.is_set("sprite"):
            raise generic.ScriptError("'sprite' must be set for this layout sprite", self.pos)

        # Make sure that recolouring is set correctly
        if self.get_param("recolour_mode") == 0 and self.is_set("palette"):
            raise generic.ScriptError("'palette' may not be set when 'recolour_mode' is RECOLOUR_NONE.")
        elif self.get_param("recolour_mode") != 0 and not self.is_set("palette"):
            raise generic.ScriptError("'palette' must be set when 'recolour_mode' is not set to RECOLOUR_NONE.")

        # Add the constant terms first
        sprite_num = self.get_param("recolour_mode") << 14
        if self.get_param("always_draw"):
            sprite_num |= 1 << 30
        if self.sprite_from_action1:
            sprite_num |= 1 << 31

        # Add the sprite
        expr = nmlop.ADD(self.get_param("sprite"), sprite_num, self.pos)
        # Add the palette
        expr = nmlop.ADD(nmlop.SHIFT_LEFT(self.get_param("palette"), 16, self.pos), expr)
        return expr.reduce()

    def get_param(self, name):
        assert name in self.params
        return self.params[name]["value"]

    def is_set(self, name):
        assert name in self.params
        return self.params[name]["is_set"]

    def get_register(self, name):
        assert name in self.params
        return self.params[name]["register"]

    def get_all_registers(self):
        return [self.get_register(name) for name in sorted(self.params) if self.get_register(name) is not None]

    def create_register(self, name, value):
        if (
            # Always copy values from "prepare_layout" into new registers, to prevent "default" from modifying them.
            self.feature != 0x04
            and isinstance(value, expression.StorageOp)
            and value.name == "LOAD_TEMP"
            and isinstance(value.register, expression.ConstantNumeric)
        ):
            store_tmp = None
            load_tmp = action2var.VarAction2Var(0x7D, 0, 0xFFFFFFFF, value.register.value)
        else:
            store_tmp = action2var.VarAction2StoreTempVar()
            load_tmp = action2var.VarAction2LoadTempVar(store_tmp)
        self.params[name]["register"] = (load_tmp, store_tmp, value)

    def set_param(self, name, value):
        assert isinstance(name, expression.Identifier)
        assert isinstance(value, expression.Expression)
        name = name.value

        if name not in self.params:
            raise generic.ScriptError("Unknown sprite parameter '{}'".format(name), value.pos)
        if self.is_set(name):
            raise generic.ScriptError("Sprite parameter '{}' can be set only once per sprite.".format(name), value.pos)

        self.params[name]["value"] = self.params[name]["validator"](name, value)
        self.params[name]["is_set"] = True

    def _validate_offset(self, offset, spriteset, pos):
        if len(offset) == 0:
            offset = None
        elif len(offset) == 1:
            id_dicts = [
                (spriteset.labels if spriteset else {}, lambda name, val, pos: expression.ConstantNumeric(val, pos))
            ]
            offset = action2var.reduce_varaction2_expr(
                offset[0], action2var.get_scope(self.feature), self.extra_dicts + id_dicts
            )
            if spriteset and isinstance(offset, expression.ConstantNumeric):
                generic.check_range(
                    offset.value,
                    0,
                    len(real_sprite.parse_sprite_data(spriteset)) - 1,
                    "offset within spriteset",
                    pos,
                )
        else:
            raise generic.ScriptError("Expected 0 or 1 parameter, got " + str(len(offset)), pos)
        return offset

    def resolve_spritegroup_ref(self, sg_ref):
        """
        Resolve a reference to a (sprite/palette) sprite group

        @param sg_ref: Reference to a sprite group
        @type sg_ref: L{SpriteGroupRef}

        @return: Sprite number (index of action1 set) to use
        @rtype: L{Expression}
        """
        spriteset = action2.resolve_spritegroup(sg_ref.name)
        offset = self._validate_offset(sg_ref.param_list, spriteset, sg_ref.pos)
        num = action1.get_action1_index(spriteset)
        generic.check_range(num, 0, (1 << 14) - 1, "sprite", sg_ref.pos)
        return expression.ConstantNumeric(num), offset

    def _validate_sprite(self, name, value):
        if isinstance(value, expression.SpriteGroupRef):
            assert self.feature != 0x04
            self.sprite_from_action1 = True
            val, offset = self.resolve_spritegroup_ref(value)
            if offset is not None:
                self.create_register(name, offset)
            return val
        elif isinstance(value, StationSpriteset):
            assert self.feature == 0x04
            self.sprite_from_action1 = True
            if value.offset is not None:
                offset = self._validate_offset(value.offset, value.spriteset, value.pos)
                if offset is not None:
                    self.create_register(name, offset)
            self.var10_for_sprite = value.var10
            return expression.ConstantNumeric(0x42D)
        else:
            self.sprite_from_action1 = False
            if isinstance(value, expression.ConstantNumeric):
                generic.check_range(value.value, 0, (1 << 14) - 1, "sprite", value.pos)
                return value
            if value.supported_by_actionD(raise_error=False):
                return value
            self.create_register(name, value)
            return expression.ConstantNumeric(0)

    def _validate_recolour_mode(self, name, value):
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Expected a compile-time constant.", value.pos)

        if value.value not in (0, 1, 2):
            raise generic.ScriptError(
                "Value of 'recolour_mode' must be RECOLOUR_NONE, RECOLOUR_TRANSPARENT or RECOLOUR_REMAP."
            )
        return value.value

    def _validate_palette(self, name, value):
        if isinstance(value, expression.SpriteGroupRef):
            assert self.feature != 0x04
            self.palette_from_action1 = True
            val, offset = self.resolve_spritegroup_ref(value)
            if offset is not None:
                self.create_register(name, offset)
            return val
        elif isinstance(value, StationSpriteset):
            assert self.feature == 0x04
            self.palette_from_action1 = True
            if value.offset is not None:
                offset = self._validate_offset(value.offset, value.spriteset, value.pos)
                if offset is not None:
                    self.create_register(name, offset)
            self.var10_for_palette = value.var10
            return expression.ConstantNumeric(0x42D)
        else:
            self.palette_from_action1 = False
            if isinstance(value, expression.ConstantNumeric):
                generic.check_range(value.value, 0, (1 << 14) - 1, "palette", value.pos)
                return value
            if value.supported_by_actionD(raise_error=False):
                return value
            self.create_register(name, value)
            return expression.ConstantNumeric(0)

    def _validate_always_draw(self, name, value):
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Expected a compile-time constant number.", value.pos)
        # Not valid for ground sprites, raise error
        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError(
                "'always_draw' may not be set for groundsprites, these are always drawn anyways.", value.pos
            )

        if value.value not in (0, 1):
            raise generic.ScriptError("Value of 'always_draw' should be 0 or 1", value.pos)
        return value.value

    def _validate_bounding_box(self, name, value):
        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError(name + " can not be set for ground sprites", value.pos)
        elif self.type == Action2LayoutSpriteType.CHILD:
            if name not in ("xoffset", "yoffset"):
                raise generic.ScriptError(name + " can not be set for child sprites", value.pos)
            if isinstance(value, expression.ConstantNumeric):
                generic.check_range(value.value, 0, 255, name, value.pos)
                return value
        else:
            assert self.type == Action2LayoutSpriteType.BUILDING
            if name in ("xoffset", "yoffset", "zoffset"):
                if isinstance(value, expression.ConstantNumeric):
                    generic.check_range(value.value, -128, 127, name, value.pos)
                    return value
            else:
                assert name in ("xextent", "yextent", "zextent")
                if not isinstance(value, expression.ConstantNumeric):
                    raise generic.ScriptError(
                        "Value of '{}' must be a compile-time constant number.".format(name), value.pos
                    )
                generic.check_range(value.value, 0, 255, name, value.pos)
                return value
        # Value must be written to a register
        self.create_register(name, value)
        if self.type == Action2LayoutSpriteType.BUILDING:
            # For building sprites, x and y registers are always written together
            if name == "xoffset" and self.get_register("yoffset") is None:
                self.create_register("yoffset", expression.ConstantNumeric(0))
            if name == "yoffset" and self.get_register("xoffset") is None:
                self.create_register("xoffset", expression.ConstantNumeric(0))
        return expression.ConstantNumeric(0)

    def _validate_hide_sprite(self, name, value):
        self.create_register(name, expression.Not(value).reduce())


class ParsedSpriteLayout:
    def __init__(self, registers=None):
        self.ground_sprite = None
        self.building_sprites = []
        self.registers = registers or []
        self.advanced = False

    def get_size(self):
        size = 5
        if self.advanced:
            size += self.ground_sprite.get_registers_size()
        for sprite in self.building_sprites:
            if sprite.type == Action2LayoutSpriteType.CHILD:
                size += 7
            else:
                size += 10
            if self.advanced:
                size += sprite.get_registers_size()
        if len(self.building_sprites) == 0 and not self.advanced:
            size += 9
        return size

    def write(self, file):
        if self.advanced:
            file.print_byte(0x40 | len(self.building_sprites))
        else:
            file.print_byte(len(self.building_sprites))
        self.ground_sprite.write_sprite_number(file)
        if self.advanced:
            self.ground_sprite.write_flags(file)
            self.ground_sprite.write_registers(file)
        file.newline()
        if len(self.building_sprites) == 0 and not self.advanced:
            file.print_dwordx(0)  # sprite number 0 == no sprite
            for _ in range(0, 5):
                file.print_byte(0)  # empty bounding box. Note that number of zeros is 5, not 6
        else:
            for sprite in self.building_sprites:
                sprite.write_sprite_number(file)
                if self.advanced:
                    sprite.write_flags(file)
                file.print_byte(sprite.get_param("xoffset").value)
                file.print_byte(sprite.get_param("yoffset").value)
                if sprite.type == Action2LayoutSpriteType.CHILD:
                    file.print_bytex(0x80)
                else:
                    # normal building sprite
                    file.print_byte(sprite.get_param("zoffset").value)
                    file.print_byte(sprite.get_param("xextent").value)
                    file.print_byte(sprite.get_param("yextent").value)
                    file.print_byte(sprite.get_param("zextent").value)
                if self.advanced:
                    sprite.write_registers(file)
                file.newline()

    def process(self, spritelayout, feature, param_map, actions, var10map=None):
        if not isinstance(param_map, list):
            param_map = [param_map]

        # Reduce all expressions, can't do that earlier as feature is not known
        all_sprite_sets = []
        layout_sprite_list = []  # Create a new structure
        for layout_sprite in spritelayout.layout_sprite_list:
            param_list = []
            layout_sprite_list.append((layout_sprite.type, layout_sprite.pos, param_list))
            for param in layout_sprite.param_list:
                param_val = action2var.reduce_varaction2_expr(param.value, action2var.get_scope(feature), param_map)
                if isinstance(param_val, expression.SpriteGroupRef):
                    spriteset = action2.resolve_spritegroup(param_val.name)
                    if not spriteset.is_spriteset():
                        raise generic.ScriptError("Expected a reference to a spriteset.", param_val.pos)
                    if feature == 0x04:
                        assert var10map is not None
                        param_val = var10map.translate(spriteset, param_val.param_list, param_val.pos)
                    else:
                        all_sprite_sets.append(spriteset)
                param_list.append((param.name, param_val))

        actions.extend(action1.add_to_action1(all_sprite_sets, feature, spritelayout.pos))

        for type, pos, param_list in layout_sprite_list:
            if type.value not in layout_sprite_types:
                raise generic.ScriptError(
                    "Invalid sprite type '{}' encountered. Expected 'ground', 'building', or 'childsprite'.".format(
                        type.value
                    ),
                    type.pos,
                )
            sprite = Action2LayoutSprite(feature, layout_sprite_types[type.value], pos, param_map)
            for name, value in param_list:
                sprite.set_param(name, value)
            self.registers.extend(sprite.get_all_registers())
            if sprite.type == Action2LayoutSpriteType.GROUND:
                if self.ground_sprite is not None:
                    raise generic.ScriptError("Sprite layout can have no more than one ground sprite", spritelayout.pos)
                self.ground_sprite = sprite
            else:
                self.building_sprites.append(sprite)

        if self.ground_sprite is None:
            if len(self.building_sprites) == 0:
                # no sprites defined at all, that's not very much.
                raise generic.ScriptError("Sprite layout requires at least one sprite", spritelayout.pos)
            # set to 0 for no ground sprite
            self.ground_sprite = Action2LayoutSprite(feature, Action2LayoutSpriteType.GROUND)
            self.ground_sprite.set_param(expression.Identifier("sprite"), expression.ConstantNumeric(0))

        self.advanced = any(x.is_advanced_sprite() for x in self.building_sprites + [self.ground_sprite])

    def write_action_value(self, actions, act6, offset):
        sprite_num = self.ground_sprite.get_sprite_number()
        sprite_num, offset = actionD.write_action_value(sprite_num, actions, act6, offset, 4)
        if self.advanced:
            offset += self.ground_sprite.get_registers_size()

        for sprite in self.building_sprites:
            sprite_num = sprite.get_sprite_number()
            sprite_num, offset = actionD.write_action_value(sprite_num, actions, act6, offset, 4)
            if self.advanced:
                offset += sprite.get_registers_size()
            offset += 3 if sprite.type == Action2LayoutSpriteType.CHILD else 6

        return offset

    def parse_registers(self, varact2parser):
        if self.registers:
            for register_info in self.registers:
                reg, expr = register_info[1], register_info[2]
                if reg is None:
                    continue
                varact2parser.parse_expr(expr)
                varact2parser.var_list.append(nmlop.STO_TMP)
                varact2parser.var_list.append(reg)
                varact2parser.var_list.append(nmlop.VAL2)
                varact2parser.var_list_size += reg.get_size() + 2


def get_layout_action2s(spritelayout, feature):
    actions = []

    if feature not in action2.features_sprite_layout:
        raise generic.ScriptError(
            "Sprite layouts are not supported for feature '{}'.".format(general.feature_name(feature))
        )

    # Allocate registers
    param_map = {}
    param_registers = []
    for param in spritelayout.param_list:
        reg = action2var.VarAction2CallParam(param.value)
        param_registers.append(reg)
        param_map[param.value] = reg
    param_map = (param_map, lambda name, value, pos: action2var.VarAction2LoadCallParam(value, name))
    spritelayout.register_map[feature] = param_registers

    layout = ParsedSpriteLayout()
    layout.process(spritelayout, feature, param_map, actions)

    action6.free_parameters.save()
    act6 = action6.Action6()

    layout.write_action_value(actions, act6, 4)

    if len(act6.modifications) > 0:
        actions.append(act6)

    layout_action = Action2Layout(
        feature,
        spritelayout.name.value + " - feature {:02X}".format(feature),
        spritelayout.pos,
        layout,
        param_registers,
    )
    actions.append(layout_action)

    varact2parser = action2var.Varaction2Parser(feature)
    layout.parse_registers(varact2parser)

    # Only continue if we actually needed any new registers
    if varact2parser.var_list:
        # Remove the last VAL2 operator
        varact2parser.var_list.pop()
        varact2parser.var_list_size -= 1

        actions.extend(varact2parser.extra_actions)
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
        if len(extra_act6.modifications) > 0:
            actions.append(extra_act6)

        varaction2 = action2var.Action2Var(
            feature, "{}@registers - feature {:02X}".format(spritelayout.name.value, feature), spritelayout.pos, 0x89
        )
        varaction2.var_list = varact2parser.var_list
        ref = expression.SpriteGroupRef(spritelayout.name, [], None, layout_action)
        varaction2.ranges.append(
            action2var.VarAction2Range(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, "")
        )
        varaction2.default_result = ref
        varaction2.default_comment = ""

        # Add two references (default + range)
        # Make sure that registers allocated here are not used by the spritelayout
        action2.add_ref(ref, varaction2, True)
        action2.add_ref(ref, varaction2, True)
        spritelayout.set_action2(varaction2, feature)
        actions.append(varaction2)
    else:
        spritelayout.set_action2(layout_action, feature)

    action6.free_parameters.restore()
    return actions


def make_empty_layout_action2(feature, pos):
    """
    Make an empty layout action2
    For use with failed callbacks

    @param feature: Feature of the sprite layout to create
    @type feature: C{int}

    @param pos: Positional context.
    @type  pos: L{Position}

    @return: The created sprite layout action2
    @rtype: L{Action2Layout}
    """
    layout = ParsedSpriteLayout()
    layout.ground_sprite = Action2LayoutSprite(feature, Action2LayoutSpriteType.GROUND)
    layout.ground_sprite.set_param(expression.Identifier("sprite"), expression.ConstantNumeric(0))
    return Action2Layout(feature, "@CB_FAILED_LAYOUT{:02X}".format(feature), pos, layout, [])


class StationSpriteset(expression.Expression):
    def __init__(self, spriteset, args, var10, pos=None):
        expression.Expression.__init__(self, pos)
        self.spriteset = spriteset
        self.offset = args
        self.var10 = var10


class StationSpritesetVar10Map:
    def __init__(self):
        self.spritesets = {}
        self.var10 = 1  # Reserving 0 for SPRITESET() (basic action2)

    def translate(self, spriteset, args, pos):
        if spriteset not in self.spritesets:
            if self.var10 == 8:
                raise generic.ScriptError("A station can't use more than 6 different sprite sets", pos)
            self.spritesets[spriteset] = self.var10
            self.var10 += 1 if self.var10 != 1 else 2  # Reserving 2 for custom foundations
        return StationSpriteset(
            None if isinstance(spriteset, int) else spriteset, args, self.spritesets[spriteset], pos
        )

    def append_mapping(self, mapping, feature, actions, default, custom_spritesets):
        for spriteset, var10 in self.spritesets.items():
            if not isinstance(spriteset, int):
                if not spriteset.has_action2(feature):
                    actions.extend(action1.add_to_action1([spriteset], feature, None))
                    real_action2 = action2real.make_simple_real_action2(
                        feature,
                        spriteset.name.value + " - feature {:02X}".format(feature),
                        None,
                        action1.get_action1_index(spriteset),
                    )
                    actions.append(real_action2)
                    spriteset.set_action2(real_action2, feature)
                ref = expression.SpriteGroupRef(spriteset.name, [], None, spriteset.get_action2(feature))
            else:
                if spriteset > len(custom_spritesets):
                    raise generic.ScriptError("Index out of range")
                ref = custom_spritesets[spriteset]
            # Skip default result
            if ref == default:
                continue
            mapping[var10] = (ref, None)
        return mapping


def parse_station_layouts(feature, id, layouts):
    var10map = StationSpritesetVar10Map()

    # Add DEFAULT([offset]) to reference active spriteset, selected by basic action2
    # and CUSTOM(index, [offset]) to reference a spriteset from the custom list
    def parse_spriteset(name, args, pos, info):
        if info:
            if len(args) < 1:
                raise generic.ScriptError("'{}' expects 1 or 2 parameters".format(name), pos)
            if not isinstance(args[0], expression.ConstantNumeric):
                raise generic.ScriptError("First parameter for '{}' must be a constant".format(name), pos)
            return var10map.translate(args[0].value, args[1:], pos)
        return StationSpriteset(None, args, info, pos)

    default_param = [
        (
            {"DEFAULT": None, "CUSTOM": True},
            lambda name, value, pos: expression.FunctionPtr(expression.Identifier(name, pos), parse_spriteset, value),
        )
    ]

    actions = []
    param_registers = []
    parsed_layouts = []
    varact2parser = action2var.Varaction2Parser(feature)

    for layout in layouts:
        spritelayout = (
            action2.resolve_spritegroup(layout.name) if isinstance(layout, expression.SpriteGroupRef) else None
        )
        if not spritelayout or not isinstance(spritelayout, spriteblock.SpriteLayout):
            raise generic.ScriptError("Expected a SpriteLayout", layout.pos)

        # Allocate registers
        registers = []
        param_map = {}
        for i, param in enumerate(spritelayout.param_list):
            reg = action2var.VarAction2CallParam(param.value)
            param_registers.append(reg)
            param_map[param.value] = reg
            store_tmp = action2var.VarAction2StoreCallParam(reg)
            registers.append((reg, store_tmp, layout.param_list[i]))
        param_map = [(param_map, lambda name, value, pos: action2var.VarAction2LoadCallParam(value, name))]
        param_map.extend(default_param)

        layout = ParsedSpriteLayout(registers)
        layout.process(spritelayout, feature, param_map, actions, var10map)
        layout.parse_registers(varact2parser)
        parsed_layouts.append(layout)

    actions.extend(action0.get_layout_action0(feature, id, parsed_layouts))

    registers_ref = None

    # Create a procedure only if needed
    if varact2parser.var_list:
        # Remove the last VAL2 operator
        varact2parser.var_list.pop()
        varact2parser.var_list_size -= 1

        actions.extend(varact2parser.extra_actions)
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
        if len(extra_act6.modifications) > 0:
            actions.append(extra_act6)

        varaction2 = action2var.Action2Var(
            feature, "Station Layout@registers - Id {:02X}".format(id.value), None, 0x89, param_registers
        )
        varaction2.var_list = varact2parser.var_list
        varaction2.default_result = expression.ConstantNumeric(0)
        varaction2.default_comment = "Return computed value"

        actions.append(varaction2)
        registers_ref = expression.SpriteGroupRef(expression.Identifier(varaction2.name), [], None, varaction2)

    return (actions, var10map, registers_ref)
