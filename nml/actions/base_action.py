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

class BaseAction(object):
    def prepare_output(self):
        """
        Called just before L{write}, this function can be used to do some
        last modifications to the action (like resolving some IDs that can't
        be resolved earlier).
        """
        pass

    def write(self, file):
        """
        Write this action to the given outputfile.

        @param file: The outputfile to write the data to.
        @type file: L{BinaryOutputBase}
        """
        raise NotImplementedError('write is not implemented in %r' % type(self))

    def skip_action7(self):
        """
        Can this action be skipped safely by an action7?

        @return True iff this action can be skipped by action7.
        """
        return True

    def skip_action9(self):
        """
        Can this action be skipped safely by an action9?

        @return True iff this action can be skipped by action9.
        """
        return True

    def skip_needed(self):
        """
        Do we need to skip this action at all?

        @return False when it doesn't matter whether this action is skipped
            or not.
        """
        return True
