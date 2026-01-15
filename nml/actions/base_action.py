# SPDX-License-Identifier: GPL-2.0-or-later


class BaseAction:
    def prepare_output(self, sprite_num):
        """
        Called just before L{write}, this function can be used to do some
        last modifications to the action (like resolving some IDs that can't
        be resolved earlier).

        @param sprite_num: The sprite number in the nfo/grf output.
        @type  sprite_num: C{int}
        """
        pass

    def write(self, file):
        """
        Write this action to the given outputfile.

        @param file: The outputfile to write the data to.
        @type  file: L{SpriteOutputBase}
        """
        raise NotImplementedError("write is not implemented in {!r}".format(type(self)))

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
