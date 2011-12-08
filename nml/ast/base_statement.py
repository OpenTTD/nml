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

from nml import generic

class BaseStatement(object):
    """
    Base class for a statement (AST node) in NML.
    Note: All instance variables (except 'pos') are prefixed with "bs_" to avoid naming conflicts

    @ivar bs_name: Name of the statement type
    @type bs_name: C{str}

    @ivar pos: Position information
    @type pos: L{Position}

    @ivar bs_skipable: Whether the statement may be skipped using an if-block (default: True)
    @type bs_skipable: C{bool}

    @ivar bs_loopable: Whether the statement may be executed multiple times using a while-block (default: True)
    @type bs_loopable: C{bool}

    @pre: bs_skipable or not bs_loopable

    @ivar bs_in_item: Whether the statement may be part of an item block (default: False_
    @type bs_in_item: C{bool}

    @ivar bs_out_item: Whether the statement may appear outside of item blocks (default: True)
    @type bs_out_item: C{bool}
    """
    def __init__(self, name, pos, skipable = True, loopable = True, in_item = False, out_item = True):
        assert skipable or not loopable
        self.bs_name = name
        self.pos = pos
        self.bs_skipable = skipable
        self.bs_loopable = loopable
        self.bs_in_item = in_item
        self.bs_out_item = out_item

    def validate(self, scope_list):
        """
        Validate that this statement is in a valid location

        @param scope_list: List of nested blocks containing this statement
        @type scope_list: C{list} of L{BaseStatementList}
        """
        seen_item = False
        for scope in scope_list:
            if scope.list_type == BaseStatementList.LIST_TYPE_SKIP:
                if not self.bs_skipable: raise generic.ScriptError("%s may not appear inside a conditional block." % self.bs_name, self.pos)
            if scope.list_type == BaseStatementList.LIST_TYPE_LOOP:
                if not self.bs_loopable: raise generic.ScriptError("%s may not appear inside a loop." % self.bs_name, self.pos)
            if scope.list_type == BaseStatementList.LIST_TYPE_ITEM:
                seen_item = True
                if not self.bs_in_item: raise generic.ScriptError("%s may not appear inside an item block." % self.bs_name, self.pos)
        if not (seen_item or self.bs_out_item):
            raise generic.ScriptError("%s must appear inside an item block." % self.bs_name, self.pos)

    def register_names(self):
        """
        Called to register identifiers, that must be available before their definition.
        """
        pass

    def pre_process(self):
        """
        Called to do any pre-processing before the actual action generation.
        For example, to remove identifiesr
        """
        pass

    def debug_print(self, indentation):
        """
        Print all AST information to the standard output

        @param indentation: Print all lines with at least C{indentation} spaces
        @type indentation: C{int}
        """
        raise NotImplementedError('debug_print must be implemented in BaseStatement-subclass %r' % type(self))

    def get_action_list(self):
        """
        Generate a list of NFO actions associated with this statement

        @return: A list of action
        @rtype: C{list} of L{BaseAction}
        """
        raise NotImplementedError('get_action_list must be implemented in BaseStatement-subclass %r' % type(self))

    def __str__(self):
        """
        Generate a string representing this statement in valid NML-code.

        @return: An NML string representing this action
        @rtype: C{str}
        """
        raise NotImplementedError('__str__ must be implemented in BaseStatement-subclass %r' % type(self))


class BaseStatementList(BaseStatement):
    """
    Base class for anything that contains a list of statements

    @ivar list_type: Type of this list, used for validation logic
    @type list_type: C{int}, see constants below
    @pre list_type in (LIST_TYPE_NONE, LIST_TYPE_SKIP, LIST_TYPE_LOOP, LIST_TYPE_ITEM)

    @ivar statements: List of sub-statements in this block
    @type statements: C{list} of L{BaseStatement}
    """
    LIST_TYPE_NONE = 0
    LIST_TYPE_SKIP = 1
    LIST_TYPE_LOOP = 2
    LIST_TYPE_ITEM = 3

    def __init__(self, name, pos, list_type, statements, skipable = True, loopable = True, in_item = False, out_item = True):
        BaseStatement.__init__(self, name, pos, skipable, loopable, in_item, out_item)
        assert list_type in (self.LIST_TYPE_NONE, self.LIST_TYPE_SKIP, self.LIST_TYPE_LOOP, self.LIST_TYPE_ITEM)
        self.list_type = list_type
        self.statements = statements

    def validate(self, scope_list):
        new_list = scope_list + [self]
        for stmt in self.statements:
            stmt.validate(new_list)

    def register_names(self):
        for stmt in self.statements:
            stmt.register_names()

    def pre_process(self):
        for stmt in self.statements:
            stmt.pre_process()

    def debug_print(self, indentation):
        for stmt in self.statements:
            stmt.debug_print(indentation)

    def get_action_list(self):
        action_list = []
        for stmt in self.statements:
            action_list.extend(stmt.get_action_list())
        return action_list

    def __str__(self):
        res = "" 
        for stmt in self.statements:
            res += '\t' + str(stmt).replace('\n', '\n\t')[0:-1]
        return res
