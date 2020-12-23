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

from nml import generic, global_constants
from nml.actions import base_action
from nml.ast import base_statement, general

total_action2_ids = 0x100
free_action2_ids = list(range(0, total_action2_ids))

"""
Statistics about spritegroups.
The 1st field of type C{int} contains the largest number of concurrently active spritegroup ids.
The 2nd field of type L{Position} contains a positional reference
  to the last spritegroup of the concurrently active ones.
"""
spritegroup_stats = (0, None)

total_tmp_locations = 0x7F

"""
Statistics about temporary Action2 registers.
The 1st field of type C{int} contains the largest number of concurrently active register ids.
The 2nd field of type L{Position} contains a positional reference to the spritegroup.
"""
a2register_stats = (0, None)


def print_stats():
    """
    Print statistics about used ids.
    """
    if spritegroup_stats[0] > 0:
        generic.print_info(
            "Concurrent spritegroups: {}/{} ({})".format(
                spritegroup_stats[0], total_action2_ids, str(spritegroup_stats[1])
            )
        )
    if a2register_stats[0] > 0:
        generic.print_info(
            "Concurrent Action2 registers: {}/{} ({})".format(
                a2register_stats[0], total_tmp_locations, str(a2register_stats[1])
            )
        )


class Action2(base_action.BaseAction):
    """
    Abstract Action2 base class.

    @ivar name: Name of the action2.
    @type name: C{str}

    @ivar feature: Action2 feature byte.
    @type feature: C{int}

    @ivar pos: Position reference to source.
    @type pos: L{Position}

    @ivar num_refs: Number of references to this action2.
    @type num_refs: C{int}

    @ivar id: Number of this action2.
    @type id: C{int}, or C{None} if no number is allocated yet.

    @ivar references: All Action2s that are referenced by this Action2.
    @type references: C{list} of L{Action2Reference}

    @ivar tmp_locations: List of address in the temporary storage that are free
                         to be used in this varaction2.
    @type tmp_locations: C{list} of C{int}
    """

    def __init__(self, feature, name, pos):
        self.feature = feature
        self.name = name
        self.pos = pos
        self.num_refs = 0
        self.id = None
        self.references = []
        # 0x00 - 0x7F: available to user
        # 0x80 - 0xFE: used by NML
        # 0xFF: Used for some house variables
        # 0x100 - 0x10F: Special meaning (used for some CB results)
        self.tmp_locations = list(range(0x80, 0x80 + total_tmp_locations))

    def prepare_output(self, sprite_num):
        free_references(self)

        global spritegroup_stats

        try:
            if self.num_refs == 0:
                self.id = free_action2_ids[0]
            else:
                self.id = free_action2_ids.pop()
                num_used = total_action2_ids - len(free_action2_ids)
                if num_used > spritegroup_stats[0]:
                    spritegroup_stats = (num_used, self.pos)
        except IndexError:
            raise generic.ScriptError(
                "Unable to allocate ID for [random]switch, sprite set/layout/group or produce-block."
                " Try reducing the number of such blocks.",
                self.pos,
            )

    def write_sprite_start(self, file, size, extra_comment=None):
        assert self.num_refs == 0, "Action2 reference counting has {:d} dangling references.".format(self.num_refs)
        file.comment("Name: " + self.name)
        if extra_comment:
            for c in extra_comment:
                file.comment(c)
        file.start_sprite(size + 3)
        file.print_bytex(2)
        file.print_bytex(self.feature)
        file.print_bytex(self.id)

    def skip_action7(self):
        return False

    def skip_action9(self):
        return False

    def skip_needed(self):
        return False

    def remove_tmp_location(self, location, force_recursive):
        """
        Recursively remove a location from the list of available temporary
        storage locations. It is not only removed from the the list of the
        current Action2Var but also from all Action2Var it calls. If an
        Action2Var is referenced as a procedure call, the location is always
        removed recursively, otherwise only if force_recursive is True.

        @param location: Number of the storage register to remove.
        @type location: C{int}

        @param force_recursive: Force removing this location recursively,
                                also for 'chained' action2s.
        @type force_recursive: C{bool}
        """
        global a2register_stats

        if location in self.tmp_locations:
            self.tmp_locations.remove(location)
            num_used = total_tmp_locations - len(self.tmp_locations)
            if num_used > a2register_stats[0]:
                a2register_stats = (num_used, self.pos)

        for act2_ref in self.references:
            if force_recursive or act2_ref.is_proc:
                act2_ref.action2.remove_tmp_location(location, True)


class Action2Reference:
    """
    Container class to store information about an action2 reference

    @ivar action2: The target action2
    @type action2: L{Action2}

    @ivar is_proc: Whether this reference is made because of a procedure call
    @type is_proc: C{bool}
    """

    def __init__(self, action2, is_proc):
        self.action2 = action2
        self.is_proc = is_proc


def add_ref(ref, source_action, reference_as_proc=False):
    """
    Add a reference to a certain action2.
    This is needed so we can correctly reserve / free action2 IDs later on.
    To be called when creating the actions from the AST.

    @param ref: Reference to the sprite group that corresponds to the action2.
    @type ref: L{SpriteGroupRef}

    @param source_action: Source action (act2 or act3) that contains the reference.
    @type source_action: L{Action2} or L{Action3}

    @param reference_as_proc: True iff the reference source is a procedure call,
                              which needs special precautions for temp registers.
    @type reference_as_proc: C{bool}
    """

    # Add reference to list of references of the source action
    act2 = ref.act2 if ref.act2 is not None else resolve_spritegroup(ref.name).get_action2(source_action.feature)
    source_action.references.append(Action2Reference(act2, reference_as_proc))
    act2.num_refs += 1


def free_references(source_action):
    """
    Free all references to other action2s from a certain action 2/3

    @param source_action: Action that contains the reference
    @type  source_action: L{Action2} or L{Action3}
    """
    for act2_ref in source_action.references:
        act2 = act2_ref.action2
        act2.num_refs -= 1
        if act2.num_refs == 0:
            free_action2_ids.append(act2.id)


# Features using sprite groups directly: vehicles, canals, cargos, railtypes, airports, roadtypes, tramtypes
features_sprite_group = [0x00, 0x01, 0x02, 0x03, 0x05, 0x0B, 0x0D, 0x10, 0x12, 0x13]
# Features using sprite layouts: stations, houses, industry tiles, objects and airport tiles
features_sprite_layout = [0x04, 0x07, 0x09, 0x0F, 0x11]
# All features that need sprite sets
features_sprite_set = features_sprite_group + features_sprite_layout


def make_sprite_group_class(cls_is_spriteset, cls_is_referenced, cls_has_explicit_feature, cls_is_relocatable=False):
    """
    Metaclass factory which makes base classes for all nodes 'Action 2 graph'
    This graph is made up of all blocks that are eventually compiled to Action2,
    which use the same name space. Spritesets do inherit from this class to make
    referencing them possible, but they are not part of the refernce graph that
    is built.

    @param cls_is_spriteset: Whether this class represents a spriteset
    @type cls_is_spriteset: C{bool}

    @param cls_is_referenced: True iff this node can be referenced by other nodes
    @type cls_is_referenced: C{bool}

    @param cls_has_explicit_feature: Whether the feature of an instance is explicitly set,
                                    or derived from nodes that link to it.
    @type cls_has_explicit_feature: C{bool}

    @param cls_is_relocatable: Whether instances of this class can be freely moved around or whether they need
                               to to be converted to nfo code at the same location as they are in the nml code.
    @type cls_is_relocatable: C{bool}

    @return: The constructed class
    @rtype: C{type}
    """

    # without either references or an explicit feature, we have nothing to base our feature on
    assert cls_is_referenced or cls_has_explicit_feature

    class ASTSpriteGroup(base_statement.BaseStatement):
        """
        Abstract base class for all AST nodes that represent a sprite group
        This handles all the relations between the various nodes

        Child classes should do the following:
            - Implement their own __init__ method
            - Call BaseStatement.__init__
            - Call initialize, pre_process and perpare_output (in that order)
            - Implement collect_references
            - Call set_action2 after generating the corresponding action2 (if applicable)

        @ivar _referencing_nodes: Set of nodes that refer to this node
        @type _referencing_nodes: C{set}

        @ivar _referenced_nodes: Set of nodes that this node refers to
        @type _referenced_nodes: C{set}

        @ivar _prepared: True iff prepare_output has already been executed
        @type _prepared: C{bool}

        @ivar _action2: Mapping of features to action2s
        @type _action2: C{dict} that maps C{int} to L{Action2}

        @ivar feature_set: Set of features that use this node
        @type feature_set: C{set} of C{int}

        @ivar name: Name of this node, as declared by the user
        @type name: L{Identifier}

        @ivar num_params: Number of parameters that can be (and have to be) passed
        @type num_params: C{int}

        @ivar used_sprite_sets: List of sprite sets used by this node
        @type used_sprite_sets: C{list} of L{SpriteSet}
        """

        def __init__(self):
            """
            Subclasses should implement their own __init__ method.
            This method should not be called, because calling a method on a meta class can be troublesome.
            Instead, call initialize(..).
            """
            raise NotImplementedError(
                (
                    "__init__ must be implemented in ASTSpriteGroup-subclass {!r},"
                    " initialize(..) should be called instead"
                ).format(type(self))
            )

        def initialize(self, name=None, feature=None, num_params=0):
            """
            Initialize this instance.
            This function is generally, but not necessarily, called from the child class' constructor.
            Calling it later (during pre-processing) is also possible, as long as it's called
            before any other actions are done.

            @param name: Name of this node, as set by the user (if applicable)
                            Should be be set (not None) iff cls_is_referenced is True
            @type name: L{Identifier} or C{None} if N/A

            @param feature: Feature of this node, if set by the user.
                                Should be set (not None) iff cls_has_explicit_feature is True
            @type feature: C{int} or C{None}
            """
            assert not (self._has_explicit_feature() and feature is None)
            assert not (cls_is_referenced and name is None)
            self._referencing_nodes = set()
            self._referenced_nodes = set()
            self._prepared = False
            self._action2 = {}
            self.feature_set = {feature} if feature is not None else set()
            self.name = name
            self.num_params = num_params
            self.used_sprite_sets = []
            self.optimised = None

        def register_names(self):
            if cls_is_relocatable and cls_is_referenced:
                register_spritegroup(self)

        def pre_process(self):
            """
            Pre-process this node.
            During this stage, the reference graph is built.
            """
            refs = self.collect_references()
            for ref in refs:
                self._add_reference(ref)
            if (not cls_is_relocatable) and cls_is_referenced:
                register_spritegroup(self)

        def prepare_act2_output(self):
            """
            Prepare this node for outputting.
            This sets the feature and makes sure it is correct.

            @return: True iff parsing of this node is needed
            @rtype: C{bool}
            """
            if not cls_is_referenced:
                return True
            if not self._prepared:
                self._prepared = True
                # copy, since we're going to modify
                ref_nodes = self._referencing_nodes.copy()
                for node in ref_nodes:
                    used = node.prepare_act2_output()
                    if not used:
                        node._remove_reference(self)

                # now determine the feature
                if self._has_explicit_feature():
                    # by this time, feature should be set
                    assert len(self.feature_set) == 1
                    for n in self._referencing_nodes:
                        if n.feature_set != self.feature_set:
                            msg = "Cannot refer to block '{}' with feature '{}', expected feature is '{}'"
                            msg = msg.format(
                                self.name.value,
                                general.feature_name(next(iter(self.feature_set))),
                                general.feature_name(n.feature_set.difference(self.feature_set).pop()),
                            )
                            raise generic.ScriptError(msg, n.pos)

                elif len(self._referencing_nodes) != 0:
                    for n in self._referencing_nodes:
                        # Add the features from all calling blocks to the set
                        self.feature_set.update(n.feature_set)

                if len(self._referencing_nodes) == 0 and (not self.optimised or self.optimised is self):
                    # if we can be 'not used', there ought to be a way to refer to this block
                    assert self.name is not None
                    generic.print_warning("Block '{}' is not referenced, ignoring.".format(self.name.value), self.pos)

            return len(self._referencing_nodes) != 0

        def referenced_nodes(self):
            """
            Get the nodes that this node refers to.
            @note: Make sure to sort this in a deterministic way when the order of items affects the output.

            @return: A set of nodes
            @rtype: C{set} of L{ASTSpriteGroup}
            """
            return self._referenced_nodes

        def referencing_nodes(self):
            """
            Get the nodes that refer to this node.
            @note: Make sure to sort this in a deterministic way when the order of items affects the output.

            @return: A set of nodes
            @rtype: C{set} of L{ASTSpriteGroup}
            """

            return self._referencing_nodes

        def optimise(self):
            """
            Optimise this sprite group.

            @return: True iff this sprite group has been optimised
            @rtype: C{bool}
            """
            return False

        def collect_references(self):
            """
            This function should collect all references to other nodes from this instance.

            @return: A collection containing all links to other nodes.
            @rtype: C{iterable} of L{SpriteGroupRef}
            """
            raise NotImplementedError(
                "collect_references must be implemented in ASTSpriteGroup-subclass {!r}".format(type(self))
            )

        def set_action2(self, action2, feature):
            """
            Set this node's resulting action2

            @param feature: Feature of the Action2
            @type feature: C{int}

            @param action2: Action2 to set
            @type action2: L{Action2}
            """
            assert feature not in self._action2
            self._action2[feature] = action2

        def get_action2(self, feature):
            """
            Get this node's resulting action2

            @param feature: Feature of the Action2
            @type feature: C{int}

            @return: Action2 to get
            @rtype: L{Action2}
            """
            assert feature in self._action2
            return self._action2[feature]

        def has_action2(self, feature):
            """
            Check, if this node already has an action2 for a given feature

            @param feature: Feature to check
            @type feature: C{int}

            @return: True iff there is an action2 for this feature
            @rtype: C{bool}
            """
            return feature in self._action2

        def _add_reference(self, target_ref):
            """
            Add a reference from C{self} to a target with a given name.

            @param target_ref: Name of the reference target
            @type target_ref: L{SpriteGroupRef}
            """

            if target_ref.name.value == "CB_FAILED":
                return

            target = resolve_spritegroup(target_ref.name)
            if target.is_spriteset():
                assert target.num_params == 0
                # Referencing a spriteset directly from graphics/[random]switch
                # Passing parameters is not possible here
                if len(target_ref.param_list) != 0:
                    raise generic.ScriptError(
                        "Passing parameters to '{}' is only possible from a spritelayout.".format(
                            target_ref.name.value
                        ),
                        target_ref.pos,
                    )

                self.used_sprite_sets.append(target)
            else:
                if len(target_ref.param_list) != target.num_params:
                    msg = "'{}' expects {:d} parameters, encountered {:d}."
                    msg = msg.format(target_ref.name.value, target.num_params, len(target_ref.param_list))
                    raise generic.ScriptError(msg, target_ref.pos)

                self._referenced_nodes.add(target)
                target._referencing_nodes.add(self)

        def _remove_reference(self, target):
            """
            Add a reference from C{self} to a target

            @param target: Existing reference target to be removed
            @type target: L{ASTSpriteGroup}
            """
            assert target in self._referenced_nodes
            assert self in target._referencing_nodes
            self._referenced_nodes.remove(target)
            target._referencing_nodes.remove(self)

        # Make metaclass arguments available outside of the class
        def is_spriteset(self):
            return cls_is_spriteset

        def _has_explicit_feature(self):
            return cls_has_explicit_feature

    return ASTSpriteGroup


# list of all registered sprite sets and sprite groups
spritegroup_list = {}


def register_spritegroup(spritegroup):
    """
    Register a sprite group, so it can be resolved by name later

    @param spritegroup: Sprite group to register
    @type spritegroup: L{ASTSpriteGroup}
    """
    name = spritegroup.name.value
    if name in spritegroup_list:
        raise generic.ScriptError("Block with name '{}' has already been defined".format(name), spritegroup.pos)
    spritegroup_list[name] = spritegroup
    global_constants.spritegroups[name] = name


def resolve_spritegroup(name):
    """
    Resolve a sprite group with a given name

    @param name: Name of the sprite group.
    @type name: L{Identifier}

    @return: The sprite group that the name refers to.
    @rtype: L{ASTSpriteGroup}
    """
    if name.value not in spritegroup_list:
        raise generic.ScriptError("Unknown identifier encountered: '{}'".format(name.value), name.pos)
    return spritegroup_list[name.value]
