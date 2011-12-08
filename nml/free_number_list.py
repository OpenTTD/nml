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

class FreeNumberList(object):
    """
    Contains a list with numbers and functions to pop one number from the list,
    to save the current state and to restore to the previous state.

    @ivar free_numbers: The list with currently unused numbers.
    @type free_numbers: C{list}

    @ivar states: A list of lists. Each sublist contains all numbers
        that were L{popped<pop>} between the last call to L{save} and
        the next call to L{save}. Every time L{save} is called one
        sublist is added, every time L{restore} is called the topmost
        sublist is removed and it's values are added to the free number
        list again.
    @type states: C{list}

    @ivar used_numbers: A set with all numbers that have been used at
        some time. This is used by L{pop_unique}.
    @type used_numbers: C{set}
    """
    def __init__(self, free_numbers):
        self.free_numbers = free_numbers
        self.states = []
        self.used_numbers = set()

    def pop(self):
        """
        Pop a free number from the list. You have to call L{save} at least
        once before calling L{pop}.

        @return: Some free number.
        """
        assert len(self.states) > 0
        assert len(self.free_numbers) > 0
        num = self.free_numbers.pop()
        self.states[-1].append(num)
        self.used_numbers.add(num)
        return num

    def pop_global(self):
        """
        Pop a free number from the list. The number may have been used before
        and already been restored but it'll never be given out again.

        @return: Some free number.
        """
        assert len(self.free_numbers) > 0
        return self.free_numbers.pop()

    def pop_unique(self):
        """
        Pop a free number from the list. The number has not been used before
        and will not be used again.

        @return: A unique free number.
        """
        available = set(self.free_numbers) - self.used_numbers
        for num in available:
            self.free_numbers.remove(num)
            self.used_numbers.add(num)
            return num
        assert False, "No unique number available"

    def save(self):
        """
        Save the current state. All calls to L{pop} will be saved and can be
        reverted by calling L{restore}
        """
        self.states.append([])

    def restore(self):
        """
        Add all numbers given out via L{pop} since the last L{save} to the free
        number list.
        """
        assert len(self.states) > 0
        self.states[-1].reverse()
        self.free_numbers.extend(self.states[-1])
        self.states.pop()
