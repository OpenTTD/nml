# SPDX-License-Identifier: GPL-2.0-or-later


class SpriteCountAction:
    def __init__(self, count):
        self.count = count

    def prepare_output(self, sprite_num):
        assert sprite_num == 0

    def write(self, file):
        file.start_sprite(4)
        file.print_dword(self.count)
        file.newline()
        file.end_sprite()
