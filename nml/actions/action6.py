# SPDX-License-Identifier: GPL-2.0-or-later

from nml import free_number_list, generic
from nml.actions import base_action

free_parameters = free_number_list.FreeNumberList(
    list(range(0x40, 0x80)),
    "No free parameters available to use for internal computations.",
    "No unique free parameters available for internal computations.",
)


def print_stats():
    """
    Print statistics about used ids.
    """
    if free_parameters.stats[0] > 0:
        generic.print_info(
            "Concurrent ActionD registers: {}/{} ({})".format(
                free_parameters.stats[0], free_parameters.total_amount, str(free_parameters.stats[1])
            )
        )


class Action6(base_action.BaseAction):
    def __init__(self):
        self.modifications = []

    def modify_bytes(self, param, num_bytes, offset):
        self.modifications.append((param, num_bytes, offset))

    def write(self, file):
        size = 2 + 5 * len(self.modifications)
        file.start_sprite(size)
        file.print_bytex(6)
        file.newline()
        for mod in self.modifications:
            file.print_bytex(mod[0])
            file.print_bytex(mod[1])
            file.print_bytex(0xFF)
            file.print_wordx(mod[2])
            file.newline()
        file.print_bytex(0xFF)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        return False
