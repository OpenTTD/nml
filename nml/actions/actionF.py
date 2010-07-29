"""
Code for storing and generating action F
"""
from nml.actions import base_action

# Helper functions to allocate townname IDs
#
# Numbers available are from 0 to 0x7f (inclusive).
# These numbers can be in five states:
# - free:            Number is available for use.
# - named:           Number is allocated to represent a name.
# - safe numbered:   Number is allocated by the user, and is safe to refer to.
# - unsafe numbered: Number is allocated by the user, and is not safe to refer to (that is, it is below the point of 'prepare_output')
# - invisible:       Number is allocated by a final town_name, without attaching a name to it. It is not accessible any more.
# Instances of the TownNames class have a 'name' attribute, which can be 'None' (for an invisible number),
# a string (for a named number), or a (constant numeric) expression (for a safe/unsafe number).
#
free_numbers = set(range(0x7f + 1)) #: Free numbers.
first_free_id = 0        #: All numbers before this are allocated.
named_numbers = {}       #: Mapping of names to named numbers. Note that these are always safe to refer to.
numbered_numbers = set() #: Safe numbers introduced by the user (without name).

def get_free_id():
    """Allocate a number from the free_numbers."""
    global first_free_id, free_numbers
    while first_free_id not in free_numbers: first_free_id = first_free_id + 1
    number = first_free_id
    free_numbers.remove(number)
    first_free_id = first_free_id + 1
    return number

town_names_blocks = {} # Mapping of town_names ID number to TownNames instance.


class ActionF(base_action.BaseAction):
    def __init__(self, town_names_data):
        self.town_names_data = town_names_data

    def prepare_output(self):
        self.town_names_data.prepare_output()

    def write(self, file):
        file.start_sprite(2 + self.town_names_data.get_length_styles() +
                self.town_names_data.get_length_parts())
        file.print_bytex(0xF)
        id = self.town_names_data.get_id()
        file.print_bytex(id)
        self.town_names_data.write_styles(file)
        file.newline()
        self.town_names_data.write_parts(file)
        file.end_sprite()

    def skip_action7(self):
        return False
