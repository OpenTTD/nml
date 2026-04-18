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

from nml import expression, generic, global_constants
from nml.actions import action2, action2layout, action2real, real_sprite
from nml.ast import base_statement, sprite_container


class TemplateDeclaration(base_statement.BaseStatement):
    def __init__(self, name, param_list, sprite_list, pos):
        base_statement.BaseStatement.__init__(self, "template declaration", pos, False, False)
        self.name = name
        self.param_list = param_list
        self.sprite_list = sprite_list

    def pre_process(self):
        # check that all templates that are referred to exist at this point
        # This prevents circular dependencies
        for sprite in self.sprite_list:
            if isinstance(sprite, real_sprite.TemplateUsage):
                if sprite.name.value == self.name.value:
                    raise generic.ScriptError(
                        "Sprite template '{}' includes itself.".format(sprite.name.value), self.pos
                    )
                elif sprite.name.value not in real_sprite.sprite_template_map:
                    raise generic.ScriptError(
                        f"Encountered unknown template identifier: {sprite.name.value}", sprite.pos
                    )
        # Register template
        if self.name.value not in real_sprite.sprite_template_map:
            real_sprite.sprite_template_map[self.name.value] = self
        else:
            raise generic.ScriptError(
                "Template named '{}' is already defined, first definition at {}".format(
                    self.name.value, real_sprite.sprite_template_map[self.name.value].pos
                ),
                self.pos,
            )

    def get_labels(self):
        labels = {}
        offset = 0
        for sprite in self.sprite_list:
            sprite_labels, num_sprites = sprite.get_labels()
            for lbl, lbl_offset in sprite_labels.items():
                if lbl in labels:
                    raise generic.ScriptError("Duplicate label encountered; '{}' already exists.".format(lbl), self.pos)
                labels[lbl] = lbl_offset + offset
            offset += num_sprites
        return labels, offset

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Template declaration:", self.name.value)
        generic.print_dbg(indentation + 2, "Parameters:")
        for param in self.param_list:
            param.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Sprites:")
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return []

    def __str__(self):
        ret = "template {}({}) {{\n".format(str(self.name), ", ".join([str(param) for param in self.param_list]))
        for sprite in self.sprite_list:
            ret += "\t{}\n".format(sprite)
        ret += "}\n"
        return ret


spriteset_base_class = action2.make_sprite_group_class(True, True, False, cls_is_relocatable=True)


class SpriteSet(spriteset_base_class, sprite_container.SpriteContainer):
    def __init__(self, param_list, sprite_list, pos):
        base_statement.BaseStatement.__init__(self, "spriteset", pos, False, False)
        if not (1 <= len(param_list) <= 5):
            raise generic.ScriptError(f"Spriteset requires 1 to 5 parameters, encountered {len(param_list)}", pos)
        name = param_list[0]
        if not isinstance(name, expression.Identifier):
            raise generic.ScriptError("Spriteset parameter 1 'name' should be an identifier", name.pos)
        sprite_container.SpriteContainer.__init__(self, "spriteset", name)
        self.initialize(name)
        self.zoom_level = 0
        self.bit_depth = 8
        self.image_file = None

        if len(param_list) >= 3:
            if isinstance(param_list[1], expression.Identifier) and param_list[1].value in global_constants.zoom_levels:
                self.zoom_level = global_constants.zoom_levels[param_list[1].value]
            else:
                raise generic.ScriptError(
                    "value for Spriteset-block parameter 2 'zoom level' is not a valid zoom level", param_list[1].pos
                )
            if isinstance(param_list[2], expression.Identifier) and param_list[2].value in global_constants.bit_depths:
                self.bit_depth = global_constants.bit_depths[param_list[2].value]
            else:
                raise generic.ScriptError(
                    "value for Spriteset-block parameter 3 'bit depth' is not a valid bit depth", param_list[2].pos
                )

            if len(param_list) >= 4:
                self.image_file = param_list[3].reduce()
                if not isinstance(self.image_file, expression.StringLiteral):
                    raise generic.ScriptError(
                        "Spriteset-block parameter 4 'file' must be a string literal", self.image_file.pos
                    )
        elif len(param_list) >= 2:
            self.image_file = param_list[1].reduce()
            if not isinstance(self.image_file, expression.StringLiteral):
                raise generic.ScriptError(
                    "Spriteset-block parameter 2 'file' must be a string literal", self.image_file.pos
                )

        if self.bit_depth == 32:
            global_constants.any_32bpp_sprites = global_constants.allow_32bpp

        if len(param_list) >= 5:
            self.mask_file = param_list[4].reduce()
            if not isinstance(self.mask_file, expression.StringLiteral):
                raise generic.ScriptError(
                    "Spriteset-block parameter 5 'mask_file' must be a string literal", self.mask_file.pos
                )
            if not self.bit_depth == 32:
                raise generic.ScriptError("A mask file may only be specified for 32 bpp sprites.", self.mask_file.pos)
        else:
            self.mask_file = None

        self.sprite_list = sprite_list
        self.action1_num = None  # set number in action1
        self.labels = {}  # mapping of real sprite labels to offsets
        self.add_sprite_data(self.sprite_list, self.image_file, pos, self.zoom_level, self.bit_depth, self.mask_file)

    def pre_process(self):
        spriteset_base_class.pre_process(self)
        offset = 0
        for sprite in self.sprite_list:
            sprite_labels, num_sprites = sprite.get_labels()
            for lbl, lbl_offset in sprite_labels.items():
                if lbl in self.labels:
                    raise generic.ScriptError("Duplicate label encountered; '{}' already exists.".format(lbl), self.pos)
                self.labels[lbl] = lbl_offset + offset
            offset += num_sprites

    def collect_references(self):
        return []

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Sprite set:", self.name.value)
        generic.print_dbg(
            indentation + 2, "Source:  ", self.image_file.value if self.image_file is not None else "None"
        )

        generic.print_dbg(indentation + 2, "Sprites:")
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        # Actions are created when parsing the action2s, not here
        return []

    def __str__(self):
        params = [
            self.name,
            generic.reverse_lookup(global_constants.zoom_levels, self.zoom_level),
            generic.reverse_lookup(global_constants.bit_depths, self.bit_depth),
        ]
        if self.image_file is not None:
            params.append(self.image_file)
        if self.mask_file is not None:
            params.append(self.mask_file)
        ret = "spriteset({}) {{\n".format(", ".join(str(p) for p in params))
        for sprite in self.sprite_list:
            ret += "\t{}\n".format(str(sprite))
        ret += "}\n"
        return ret


spritegroup_base_class = action2.make_sprite_group_class(False, True, False)


class SpriteGroup(spritegroup_base_class):
    def __init__(self, name, spriteview_list, pos=None):
        base_statement.BaseStatement.__init__(self, "spritegroup", pos, False, False)
        self.initialize(name)
        self.spriteview_list = spriteview_list

    def pre_process(self):
        for spriteview in self.spriteview_list:
            spriteview.pre_process()
        spritegroup_base_class.pre_process(self)

    def collect_references(self):
        return []

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Sprite group:", self.name.value)
        for spriteview in self.spriteview_list:
            spriteview.debug_print(indentation + 2)

    def get_action_list(self):
        action_list = []
        if self.prepare_act2_output():
            for feature in sorted(self.feature_set):
                action_list.extend(action2real.get_real_action2s(self, feature))
        return action_list

    def __str__(self):
        ret = "spritegroup {} {{\n".format(self.name)
        for spriteview in self.spriteview_list:
            ret += "\t{}\n".format(spriteview)
        ret += "}\n"
        return ret


class SpriteView:
    def __init__(self, name, spriteset_list, pos):
        self.name = name
        self.spriteset_list = spriteset_list
        self.pos = pos

    def pre_process(self):
        self.spriteset_list = [x.reduce(global_constants.const_list) for x in self.spriteset_list]
        for sg_ref in self.spriteset_list:
            if not (
                isinstance(sg_ref, expression.SpriteGroupRef)
                and action2.resolve_spritegroup(sg_ref.name).is_spriteset()
            ):
                raise generic.ScriptError("Expected a sprite set reference", sg_ref.pos)
            if len(sg_ref.param_list) != 0:
                raise generic.ScriptError(
                    "Spritesets referenced from a spritegroup may not have parameters.", sg_ref.pos
                )

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Sprite view:", self.name.value)
        generic.print_dbg(indentation + 2, "Sprite sets:")
        for spriteset in self.spriteset_list:
            spriteset.debug_print(indentation + 4)

    def __str__(self):
        return "{}: [{}];".format(self.name, ", ".join([str(spriteset) for spriteset in self.spriteset_list]))


spritelayout_base_class = action2.make_sprite_group_class(False, True, False)


class SpriteLayout(spritelayout_base_class):
    def __init__(self, name, param_list, layout_sprite_list, pos=None):
        base_statement.BaseStatement.__init__(self, "spritelayout", pos, False, False)
        self.initialize(name, None, len(param_list))
        self.param_list = param_list
        self.register_map = {}  # Set during action generation for easier referencing
        self.layout_sprite_list = layout_sprite_list

    # Do not reduce expressions here as they may contain variables
    # And the feature is not known yet
    def pre_process(self):
        # Check parameter names
        seen_names = set()
        for param in self.param_list:
            if not isinstance(param, expression.Identifier):
                raise generic.ScriptError("spritelayout parameter names must be identifiers.", param.pos)
            if param.value in seen_names:
                raise generic.ScriptError("Duplicate parameter name '{}' encountered.".format(param.value), param.pos)
            seen_names.add(param.value)
        spritelayout_base_class.pre_process(self)

    def collect_references(self):
        return []

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Sprite layout:", self.name.value)
        generic.print_dbg(indentation + 2, "Parameters:")
        for param in self.param_list:
            param.debug_print(indentation + 4)
        generic.print_dbg(indentation + 2, "Sprites:")
        for layout_sprite in self.layout_sprite_list:
            layout_sprite.debug_print(indentation + 4)

    def __str__(self):
        params = "" if not self.param_list else "({})".format(", ".join(str(x) for x in self.param_list))
        return "spritelayout {}{} {{\n{}\n}}\n".format(
            str(self.name), params, "\n".join(str(x) for x in self.layout_sprite_list)
        )

    def get_action_list(self):
        action_list = []
        if self.prepare_act2_output():
            for feature in sorted(self.feature_set):
                if feature == 0x04:
                    continue
                action_list.extend(action2layout.get_layout_action2s(self, feature))
        return action_list


class LayoutSprite:
    def __init__(self, ls_type, param_list, pos):
        self.type = ls_type
        self.param_list = param_list
        self.pos = pos

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Tile layout sprite of type:", self.type)
        for layout_param in self.param_list:
            layout_param.debug_print(indentation + 2)

    def __str__(self):
        return "\t{} {{\n\t\t{}\n\t}}".format(
            self.type, "\n\t\t".join(str(layout_param) for layout_param in self.param_list)
        )
