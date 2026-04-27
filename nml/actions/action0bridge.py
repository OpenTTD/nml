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

"""
Bridges (feature 0x06) -- sprite-table lowering for prop 0x0D.

Called from GraphicsBlock when item_feature == 0x06.  Each bridge's
``graphics { bridge_back: [...]; bridge_front: [...]; bridge_pillars: [...]; bridge_head: [...]; }`` block:

  ``bridge_back``    48 sprites  (4 transports x 6 tables x 2 coords)
  ``bridge_front``   48 sprites
  ``bridge_pillars`` 48 sprites
  ``bridge_head``    32 sprites  (table 6 / BRIDGE_PIECE_HEAD: 4 transports x flat/ramp x 4 sub-slots)

All four are optional.  Unique sprites across every bridge in a compile share a
single GRM reservation and a single ActionA sprite-load sequence, emitted once
before the first bridge's Action0.  Each bridge's Action0 is patched via
Action6 so the 16-bit sprite-ID word of every prop 0x0D slot = GRM_base + idx.

GRM base is stored in user param register 0x3F.  That register is reserved at
the top of the user-param space (0x00-0x3F) because the internal Action6 pool
(0x40-0x7F) is transient -- popped registers there are re-issued after each
save/restore scope, whereas the GRM base written at compile start must survive
until every bridge's Action0 is emitted.  If the user has already claimed
register 0x3F, a ScriptError is raised.

Two entry points, one per compilation phase:
  ``collect(graphics_block, pos)``       -- GraphicsBlock.pre_process: registers
                                            this bridge's sprites in the shared
                                            registry.  Idempotent.
  ``emit_actions(graphics_block, bridge_id, pos)``
                                          -- GraphicsBlock.get_action_list:
                                            emits the shared prelude (once) and
                                            this bridge's Action6 + Action0.
"""

from nml import expression, generic, global_constants, nmlop
from nml.actions import action2, action6, real_sprite
from nml.actions.action0 import Action0
from nml.actions.action0properties import BaseAction0Property
from nml.actions.actionA import ActionA
from nml.actions.actionD import ActionD
from nml.ast.spriteblock import SpriteSet

# ---- Constants ----

_GRM_FEATURE = 0x08  # bridges GRM feature byte
_BRIDGE_PARAM = 0x3F  # user-param slot reserved for the GRM base register

# Action0 header: action(1) + feature(1) + numprops(1) + numinfo(1)
#               + id_high(1) + id_word(2). Prop data starts at offset 7.
_ACTION0_HDR = 7

# ActionA layout: action(1) + num_sets(1) + num_per_set(1) + first_sprite(2)
# The first_sprite word sits at offset 3.
_ACTIONA_FIRST_SPRITE_OFFSET = 3


# ---- Transpose tables ----
# Input index within each 48-sprite array: i = g * 12 + t * 2 + c
#   g in 0..3  transport (rail=0, road=1, mono=2, maglev=3)
#   t in 0..5  piece (0=BRIDGE_PIECE_NORTH, 1=BRIDGE_PIECE_SOUTH,
#              2=BRIDGE_PIECE_INNER_NORTH, 3=BRIDGE_PIECE_INNER_SOUTH,
#              4=BRIDGE_PIECE_MIDDLE_ODD,  5=BRIDGE_PIECE_MIDDLE_EVEN)
#   c in 0..1  coord (X=0, Y=1)
#
# NFO slot within BridgePartsProp (6 tables x 32 DWORDs = 192):
#   slot = t * 32 + g * 8 + c * 4 + tp
#   tp = 0 for back, 1 for front, 2 for pillars
#   (tp == 3 slots are reserved, never written)

_BACK_TO_NFO = [0] * 48
_FRONT_TO_NFO = [0] * 48
_PILLARS_TO_NFO = [0] * 48
for _g in range(4):
    for _t in range(6):
        for _c in range(2):
            _i = _g * 12 + _t * 2 + _c
            _BACK_TO_NFO[_i] = _t * 32 + _g * 8 + _c * 4 + 0
            _FRONT_TO_NFO[_i] = _t * 32 + _g * 8 + _c * 4 + 1
            _PILLARS_TO_NFO[_i] = _t * 32 + _g * 8 + _c * 4 + 2


# ---- Sprite key helpers ----


def _rs_key(rs):
    """Structural key for one RealSprite (one zoom/bpp variant of a slot)."""
    mp = getattr(rs, "mask_pos", None)
    return (
        rs.file.value,
        rs.xpos.value if rs.xpos is not None else None,
        rs.ypos.value if rs.ypos is not None else None,
        rs.xsize.value if rs.xsize is not None else None,
        rs.ysize.value if rs.ysize is not None else None,
        rs.xrel.value,
        rs.yrel.value,
        rs.mask_file.value if getattr(rs, "mask_file", None) is not None else None,
        (mp[0].value, mp[1].value) if mp is not None else None,
        rs.flags.value if getattr(rs, "flags", None) is not None else 0,
        getattr(rs, "bit_depth", 8),
        getattr(rs, "zoom_level", 0),
    )


def _sprite_key(rsa):
    """Hashes every zoom/bpp variant of a RealSpriteAction -- two slots that share
    an 8bpp primary but differ in alts must not collapse."""
    return tuple(_rs_key(rs) for rs in rsa.sprite_list)


def _is_empty_rsa(rsa):
    """True if this RealSpriteAction came from a blank ``[]`` literal -- its
    underlying RealSprite has no parameters and ``is_empty`` is set. Such
    slots map to dword=0 with no GRM patch."""
    return bool(rsa.sprite_list) and getattr(rsa.sprite_list[0], "is_empty", False)


# ---- Property classes ----


class BridgePartsProp(BaseAction0Property):
    """Prop 0x0D entry: tableid=0, numtables=6, 192 DWORDs (tables 0-5)."""

    TOTAL_DWORDS = 192
    HEADER_LEN = 3  # prop-num + tableid + numtables

    def __init__(self, dwords):
        assert len(dwords) == self.TOTAL_DWORDS
        self.dwords = dwords

    def write(self, file):
        file.print_bytex(0x0D)
        file.print_byte(0)
        file.print_byte(6)
        file.newline()
        for t in range(6):
            for i in range(32):
                file.print_dwordx(self.dwords[t * 32 + i])
            file.newline()

    def get_size(self):
        return self.HEADER_LEN + self.TOTAL_DWORDS * 4  # 3 + 768 = 771


class BridgeEndsProp(BaseAction0Property):
    """Prop 0x0D entry: tableid=6, numtables=1, 32 DWORDs (table 6)."""

    TOTAL_DWORDS = 32
    HEADER_LEN = 3

    def __init__(self, dwords):
        assert len(dwords) == self.TOTAL_DWORDS
        self.dwords = dwords

    def write(self, file):
        file.print_bytex(0x0D)
        file.print_byte(6)
        file.print_byte(1)
        file.newline()
        for i in range(32):
            file.print_dwordx(self.dwords[i])
        file.newline()

    def get_size(self):
        return self.HEADER_LEN + self.TOTAL_DWORDS * 4  # 3 + 128 = 131


# ---- BridgeSpriteRegistry ----


class BridgeSpriteRegistry:
    """Shared across every bridge in one compile: interns unique sprites into a
    global pool and emits the one-shot GRM reservation + ActionA sprite-load
    prelude. Each bridge's Action0 prop 0x0D slots are later patched to
    GRM_base + <global index>."""

    def __init__(self):
        self._sprite_to_index = {}  # sprite_key -> global index
        self._unique = []  # unique RealSpriteActions in insertion order
        self._prelude_emitted = False

    def intern(self, sprites):
        """Register a flat list of RealSpriteActions. Idempotent -- repeated
        calls with the same sprites return the same indices. Empty (``[]``)
        sprites are not interned; their entry in the returned list is
        ``None``, signalling callers to leave the dword at 0 and skip the
        GRM patch."""
        indices = []
        for rsa in sprites:
            if _is_empty_rsa(rsa):
                indices.append(None)
                continue
            k = _sprite_key(rsa)
            if k not in self._sprite_to_index:
                self._sprite_to_index[k] = len(self._unique)
                self._unique.append(rsa)
            indices.append(self._sprite_to_index[k])
        return indices

    def is_empty(self):
        return not self._unique

    def needs_prelude(self):
        return not self._prelude_emitted

    def build_prelude(self, pos):
        """ActionD (GRM reserve N -> param 0x3F) + chunks of Action6+ActionA+sprites.
        Each ActionA chunk holds up to 255 sprites. Action6 patches the ActionA
        first_sprite word (2 bytes at offset 3) by adding _BRIDGE_PARAM, so the
        per-chunk first_sprite = GRM_base + chunk_offset. Sets the emitted flag."""
        from nml.ast import grf as grf_mod

        # grf_mod.param_stats[0] tracks (highest_user_param_num + 1); > _BRIDGE_PARAM
        # means the user has declared a parameter at 0x3F (which we'd overwrite).
        if grf_mod.param_stats[0] > _BRIDGE_PARAM:
            raise generic.ScriptError(
                "GRF parameter 0x{:02X} is reserved for bridge sprite loading when a bridge defines graphics. "
                "Move your parameter to a lower index (< 0x{:02X}) or remove the bridge's graphics block.".format(
                    _BRIDGE_PARAM, _BRIDGE_PARAM
                ),
                pos,
            )

        n = len(self._unique)
        grm_data = expression.ConstantNumeric(0xFF | (_GRM_FEATURE << 8) | (n << 16))
        out = [
            ActionD(
                expression.ConstantNumeric(_BRIDGE_PARAM),
                expression.ConstantNumeric(0x00),
                nmlop.ASSIGN,
                expression.ConstantNumeric(0xFE),
                grm_data,
            )
        ]
        idx = 0
        while idx < n:
            k = min(n - idx, 255)
            act6 = action6.Action6()
            act6.modify_bytes(_BRIDGE_PARAM, 0x82, _ACTIONA_FIRST_SPRITE_OFFSET)
            out.append(act6)
            out.append(ActionA([(k, idx)]))
            out.extend(self._unique[idx : idx + k])
            idx += k

        self._prelude_emitted = True
        return out


# ---- BridgeGraphics ----


class BridgeGraphics:
    """One bridge's ``graphics { }`` block. Parses + validates role attributes
    and resolves each into a flat list of RealSpriteActions. Constructed in
    both phases -- the registry dedupes so re-running is cheap."""

    # (role_name, expected_sprite_count, parts_transpose_table_or_None)
    # bridge_head (BRIDGE_PIECE_HEAD) has its own prop; its transpose table is None.
    ROLES = (
        ("bridge_back", 48, _BACK_TO_NFO),
        ("bridge_front", 48, _FRONT_TO_NFO),
        ("bridge_pillars", 48, _PILLARS_TO_NFO),
        ("bridge_head", 32, None),
    )
    _ROLE_NAMES = tuple(r[0] for r in ROLES)
    _PARTS_ROLES = tuple(r[0] for r in ROLES if r[2] is not None)
    _ENDS_ROLE = "bridge_head"

    def __init__(self, graphics_block, pos):
        self.pos = pos
        self._sprites = {role: None for role in self._ROLE_NAMES}
        self._parse(graphics_block)

    def _parse(self, graphics_block):
        if graphics_block.default_graphics is not None:
            raise generic.ScriptError(
                "graphics for bridges does not accept a default / returned value",
                graphics_block.default_graphics.pos,
            )

        values = {role: None for role in self._ROLE_NAMES}
        for gdef in graphics_block.graphics_list:
            name = gdef.cargo_id
            if not isinstance(name, expression.Identifier) or name.value not in values:
                raise generic.ScriptError(
                    "graphics for bridges: unknown attribute; expected one of "
                    "bridge_back, bridge_front, bridge_pillars, bridge_head",
                    name.pos,
                )
            if values[name.value] is not None:
                raise generic.ScriptError(
                    "graphics for bridges: duplicate '{}' attribute".format(name.value),
                    name.pos,
                )
            if gdef.result.value is None:
                raise generic.ScriptError(
                    "graphics for bridges: 'return' is not allowed",
                    gdef.result.pos,
                )
            values[name.value] = gdef.result.value.reduce(global_constants.const_list)

        for role, expected, _ in self.ROLES:
            value = values[role]
            if value is not None:
                self._sprites[role] = self._resolve_and_flatten(value, expected, role)

    @staticmethod
    def _resolve_and_flatten(value, expected, role):
        if not isinstance(value, expression.Array):
            raise generic.ScriptError(
                "graphics: '{}' requires an array of spriteset references".format(role), value.pos
            )
        sprites = []
        for elem in value.values:
            if isinstance(elem, expression.SpriteGroupRef):
                name = elem.name
            elif isinstance(elem, (expression.Identifier, expression.StringLiteral)):
                name = elem
            else:
                raise generic.ScriptError("Each element must be a spriteset name", elem.pos)
            sg = action2.resolve_spritegroup(name)
            if not isinstance(sg, SpriteSet):
                raise generic.ScriptError("'{}' is not a spriteset".format(name.value), elem.pos)
            sprites.extend(real_sprite.parse_sprite_data(sg))
        if len(sprites) != expected:
            raise generic.ScriptError(
                "graphics: '{}' must total exactly {:d} sprites ({:d} provided)".format(role, expected, len(sprites)),
                value.pos,
            )
        return sprites

    def register(self, registry):
        """Phase 1 (GraphicsBlock.pre_process). Interns all role sprites into
        the shared registry. Returned indices are discarded."""
        for sprites in self._sprites.values():
            if sprites is not None:
                registry.intern(sprites)

    def emit(self, registry, bridge_id):
        """Phase 2 (GraphicsBlock.get_action_list). Looks up indices via the
        (now fully populated) registry and builds this bridge's Action6 +
        Action0. Returns [] if no roles were provided."""
        indices_by_role = {
            role: registry.intern(sprites) if sprites is not None else None for role, sprites in self._sprites.items()
        }

        props = []
        mods = []  # (param, size_byte, absolute_byte_offset)
        prop_offset = 0

        built = self._build_parts_prop(indices_by_role)
        if built is not None:
            parts_prop, written = built
            props.append(parts_prop)
            # Only patch slots we actually wrote. Unwritten slots (missing
            # role or `[]` blank) stay 0 -- adding GRM_base would wrongly
            # turn them into the first bridge sprite. 0x82 = 2-byte add on
            # the sprite-ID word only; leaves the palette word untouched.
            for slot in sorted(written):
                mods.append((_BRIDGE_PARAM, 0x82, _ACTION0_HDR + prop_offset + BridgePartsProp.HEADER_LEN + slot * 4))
            prop_offset += parts_prop.get_size()

        ends_built = self._build_ends_prop(indices_by_role[self._ENDS_ROLE])
        if ends_built is not None:
            ends_prop, ends_written = ends_built
            props.append(ends_prop)
            for i in sorted(ends_written):
                mods.append((_BRIDGE_PARAM, 0x82, _ACTION0_HDR + prop_offset + BridgeEndsProp.HEADER_LEN + i * 4))
            prop_offset += ends_prop.get_size()

        if not props:
            return []

        out = []
        act6 = action6.Action6()
        for param, size_byte, abs_off in mods:
            act6.modify_bytes(param, size_byte, abs_off)
        if act6.modifications:
            out.append(act6)

        act0 = Action0(0x06, bridge_id.value)
        act0.prop_list = props
        act0.num_ids = 1
        out.append(act0)

        return out

    @classmethod
    def _build_parts_prop(cls, indices_by_role):
        """Merges bridge_back/front/pillars indices into the single 192-DWORD
        BridgePartsProp. Returns (prop, written_slots) or None when none of
        the three parts roles are provided. ``None`` entries inside an
        indices list (`[]` blank slots) leave the dword at 0 and stay out
        of ``written``."""
        if all(indices_by_role[r] is None for r in cls._PARTS_ROLES):
            return None
        dwords = [0] * BridgePartsProp.TOTAL_DWORDS
        written = set()
        for role, _, slot_table in cls.ROLES:
            if slot_table is None:
                continue
            m = indices_by_role[role]
            if m is None:
                continue
            for i, uniq_idx in enumerate(m):
                if uniq_idx is None:
                    continue
                slot = slot_table[i]
                dwords[slot] = uniq_idx
                written.add(slot)
        return BridgePartsProp(dwords), written

    @staticmethod
    def _build_ends_prop(indices):
        """Returns (prop, written_slots) or None when bridge_head is missing.
        ``None`` entries inside the indices list (`[]` blank slots) become
        dword=0 and are excluded from ``written_slots`` so they aren't
        patched with the GRM base offset."""
        if indices is None:
            return None
        dwords = [0 if idx is None else idx for idx in indices]
        written = {i for i, idx in enumerate(indices) if idx is not None}
        return BridgeEndsProp(dwords), written


# ---- Module singleton + entry points ----

_registry = BridgeSpriteRegistry()


def collect(graphics_block, pos):
    """Phase 1 -- called from GraphicsBlock.pre_process for bridge items.
    Validates the graphics block and registers its sprites in the shared
    registry so the prelude can reserve GRM space for all bridges together."""
    BridgeGraphics(graphics_block, pos).register(_registry)


def emit_actions(graphics_block, bridge_id, pos):
    """Phase 2 -- called from GraphicsBlock.get_action_list for bridge items.
    Emits the shared prelude on first use (ActionD + ActionA + sprites),
    followed by this bridge's Action6 + Action0."""
    bridge = BridgeGraphics(graphics_block, pos)
    out = []
    if _registry.needs_prelude():
        if _registry.is_empty():
            raise generic.ScriptError(
                "bridge graphics block has no sprites -- provide at least one of "
                "bridge_back/bridge_front/bridge_pillars/bridge_head",
                pos,
            )
        out.extend(_registry.build_prelude(pos))
    out.extend(bridge.emit(_registry, bridge_id))
    return out
