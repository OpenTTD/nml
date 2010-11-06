from nml import generic
from nml.actions import base_action

free_action2_ids = range(1, 255)

action2_map = {}

class Action2(base_action.BaseAction):
    """
    Abstract Action2 base class.

    @ivar name; Name of the action2.
    @type name: C{str}

    @ivar feature: Action2 feature byte.
    @type feature: C{int}

    @ivar num_refs: Number of references to this action2.
    @type num_refs: C{int}

    @ivar id: Number of this action2.
    @type id: C{int}, or C{None} if no number is allocated yet.

    @ivar references: All Action2's that are references by this Action2.
    @type references: C{set}
    """
    def __init__(self, feature, name):
        global action2_map
        if name in action2_map:
            raise generic.ScriptError('Reusing names of switch/spritegroup blocks is not allowed, trying to use "%s"' % name)
        action2_map[name] = self

        self.feature = feature
        self.name = name
        self.num_refs = 0
        self.id = None
        self.references = set()

    def prepare_output(self):
        global free_action2_ids
        if self.num_refs == 0:
            self.id = free_action2_ids[0]
        else:
            self.id = free_action2_ids.pop()

    def write_sprite_start(self, file, size):
        file.comment("Name: " + self.name)
        file.start_sprite(size + 3)
        file.print_bytex(2)
        file.print_bytex(self.feature)
        file.print_bytex(self.id)

    def skip_action7(self):
        return False

    def skip_action9(self):
        return False

    def remove_tmp_location(self, location):
        """
        Recursively remove a location from the list of available temporary
        storage locations. It is not only removed from the the list of the
        current Action2Var but also from all Action2Var it calls.
        """
        if location not in self.tmp_locations: return
        self.tmp_locations.remove(location)
        for act2 in self.references:
            if isinstance(act2, Action2Var):
                act2.remove_tmp_location(location)

def add_ref(name, pos):
    global action2_map
    if name not in action2_map: raise generic.ScriptError("Referencing unknown action2 id: " + name, pos)
    action2_map[name].num_refs += 1
    return action2_map[name]

def remove_ref(name):
    if name == 'CB_FAILED': return 0
    global action2_map, free_action2_ids
    act2 = action2_map[name]
    id = act2.id
    act2.num_refs -= 1
    if act2.num_refs == 0: free_action2_ids.append(act2.id)
    return id

# Features using sprite groups directly: vehicles, canals, cargos, railtypes, airports
features_sprite_group = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0D, 0x10]
# Features using sprite layouts: stations, houses, industry tiles, objects and airport tiles
features_sprite_layout = [0x04, 0x07, 0x09, 0x0F, 0x11]
# All features that need sprite sets
features_sprite_set = features_sprite_group + features_sprite_layout

class SpriteGroupRefType:
    """
    'Enum'-class that stores the various types of references that are possible
    """
    NONE = 0 # No possible references
    SPRITESET = 1 # References to sprite sets
    SPRITEGROUP = 2 # References to sprite groups
    ALL = 3 # References to both sprite sets and groups

def make_sprite_group_class(cls_own_type, cls_referring_to_type, cls_referred_by_type, cls_has_explicit_feature):
    """
    Metaclass factory which makes base classes for all nodes 'Action 2 graph'
    This graph is made up of all blocks that are eventually compiled to Action2,
    which use the same name space.

    @param cls_own_type: Type of instances of this class
    @type cls_own_type: C{int} (values from L{SpriteGroupRefType})

    @param cls_referring_to_type: Types of items that instances of this class may refer to
    @type cls_referring_to_type: C{int} (values from L{SpriteGroupRefType})

    @param cls_referred_by_type: Types of items that may refer to an instance of this class
    @type cls_referred_by_type: C{int} (values from L{SpriteGroupRefType})

    @param cls_has_explicit_feature: Whether the feature of an instance is explicitly set,
                                    or derived from nodes that link to it.
    @type cls_has_explicit_feature: C{bool}

    @return: The constructed class
    @rtype: C{type}
    """
    #without either references or an explicit feature, we have nothing to base our feature on
    assert cls_referred_by_type != SpriteGroupRefType.NONE or cls_has_explicit_feature

    class ASTSpriteGroup(object):
        """
        Abstract base class for all AST nodes that represent a sprite group
        This handles all the relations between the various nodes

        Child classes should do the following:
            - Implement their own __init__ method
            - Call initialize, pre_process and perpare_output (in that order)
            - Implement collect_references

        @ivar _referencing_nodes: Set of nodes that refer to this node
        @type _referencing_nodes: C{set}

        @ivar _referenced_nodes: Set of nodes that this node refers to
        @type _referenced_nodes: C{set}

        @ivar feature: Feature of this node
        @type feature: L{ConstantNumeric}

        @ivar name: Name of this node, as declared by the user
        @type name: L{Identifier}
        """
        def __init__(self):
            """
            Subclasses should implement their own __init__ method.
            This method should not be called, because calling a method on a meta class can be troublesome.
            Instead, call initialize(..).
            """
            raise NotImplementedError('__init__ must be implemented in ASTSpriteGroup-subclass %r, initialize(..) should be called instead' % type(self))

        def initialize(self, name = None, feature = None):
            """
            Initialize this instance.
            This function is generally, but not necessarily, called from the child class' constructor.
            Calling it later (during pre-processing) is also possible, as long as it's called
            before any other actions are done.

            @param name: Name of this node, as set by the user
                            Should be be set (not None) iff cls_referred_by_type != SpriteGroupRefType.NONE
            @type name: L{Identifier}

            @param feature: Feature of this node, if set by the user.
                                Should be set (not None) iff cls_has_explicit_feature is True
            @type feature: L{ConstantNumeric}
            """
            assert not (self._has_explicit_feature() and feature is None)
            assert self._referred_by_type() == SpriteGroupRefType.NONE or name is not None
            self._referencing_nodes = set()
            self._referenced_nodes = set()
            self.feature = feature
            self.name = name
            self._prepared = False

        def pre_process(self):
            """
            Pre-process this node.
            During this stage, the reference graph is built.
            """
            if self._referred_by_type() != SpriteGroupRefType.NONE:
                register_spritegroup(self)
            if self._referring_to_type() != SpriteGroupRefType.NONE:
                refs = self.collect_references()
                for ref in refs:
                    self._add_reference(ref)

        def prepare_output(self):
            """
            Prepare this node for outputting.
            This sets the feature and makes sure it is correct.

            @return: True iff parsing of this node is needed
            @rtype: C{bool}
            """
            if self._referred_by_type() == SpriteGroupRefType.NONE: return True
            if not self._prepared:
                self._prepared = True
                # copy, since we're going to modify
                ref_nodes = self._referencing_nodes.copy()
                for node in ref_nodes:
                    used = node.prepare_output()
                    if not used:
                        node._remove_reference(self)

                # now determine the feature
                if self._has_explicit_feature():
                    # by this time, feature should be set
                    assert self.feature is not None
                elif len(self._referencing_nodes) != 0:
                    for n in self._referencing_nodes:
                        # get the feature of the first item in the set
                        self.feature = n.feature
                        break
                else:
                    # No one is referring to us. Let's face it, we're useless
                    return False

                for node in self._referencing_nodes:
                    if node.feature.value != self.feature.value:
                        if self._has_explicit_feature():
                            msg = "Cannot refer to block '%s' with feature %s, expected feature is %s" 
                        else:
                            msg = "Block '%s' cannot be used for feature %s (already used for feature %s)"
                        raise generic.ScriptError(msg % (self.name.value, generic.to_hex(self.feature.value, 2), generic.to_hex(node.feature.value, 2)), node.pos)
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

        def collect_references(self):
            """
            This function should collect all references to other nodes from this instance.
            It must be implemented and called iff the C{cls_referring_to_type} metaclass parameter is not 0

            @return: A collection containing all links to other nodes.
            @rtype: C{iterable} of L{SpriteGroupRef}
            """
            assert self._referring_to_type() != SpriteGroupRefType.NONE
            raise NotImplementedError('collect_references must be implemented in ASTSpriteGroup-subclass %r' % type(self))

        def _add_reference(self, target_name):
            """
            Add a reference from C{self} to a target with a given name.

            @param target_name: Name of the reference target
            @type target_name: L{SpriteGroupRef}
            """

            target = resolve_spritegroup(target_name.name, None, True, True)
            if (target._own_type() & self._referring_to_type() == 0) or \
                    (self._own_type() & target._referred_by_type() == 0):
                raise generic.ScriptError("Encountered an incorrect type of reference: '%s'" % target_name.name.value, target_name.pos)
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

        #Make metaclass arguments available
        def _own_type(self):
            return cls_own_type

        def _referring_to_type(self):
            return cls_referring_to_type

        def _referred_by_type(self):
            return cls_referred_by_type

        def _has_explicit_feature(self):
            return cls_has_explicit_feature

    return ASTSpriteGroup

#list of all registered sprite sets and sprite groups
spritegroup_list = {}

def register_spritegroup(spritegroup):
    """
    Register a sprite group, so it can be resolved by name later

    @param spritegroup: Sprite group to register
    @type spritegroup: L{ASTSpriteGroup}
    """
    name = spritegroup.name.value
    if name in spritegroup_list:
        raise generic.ScriptError("Block with name '%s' has already been defined" % name, spritegroup.pos)
    spritegroup_list[name] = spritegroup

def resolve_spritegroup(name, feature = None, allow_group = True, allow_set = True):
    """
    Resolve a sprite group with a given name

    @param name: Name of the sprite group.
    @type name: L{Identifier}

    @return: The sprite group that the name refers to.
    @rtype: L{ASTSpriteGroup}
    """
    if name.value not in spritegroup_list:
        raise generic.ScriptError("Unknown identifier encountered: '%s'" % name.value, name.pos)
    return spritegroup_list[name.value]


class SpriteGroupRef(object):
    """
    Container for a reference to a sprite group / layout

    @ivar name: Name of the referenced item
    @type name: L{Identifier}

    @ivar param_list: List of parameters to be passed
    @type param_list: C{list} of L{Expression}
    """
    def __init__(self, name, param_list, pos):
        self.name = name
        self.param_list = param_list
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' +'Reference to:' + str(self.name)
        if len(self.param_list) != 0:
            print 'Parameters:'
            for p in self.param_list:
                p.debug_print(indentation + 2)
