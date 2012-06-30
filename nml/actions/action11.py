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
Action 11 support classes (sounds).
"""
import os
from operator import itemgetter
from nml import generic
from nml.actions import base_action, action0

class Action11(base_action.BaseAction):
    def __init__(self, num_sounds):
        self.num_sounds = num_sounds

    def write(self, file):
        file.start_sprite(3)
        file.print_bytex(0x11)
        file.print_word(self.num_sounds)
        file.end_sprite()


class LoadBinaryFile(base_action.BaseAction):
    '''
    <sprite-number> * <length> FF <name-len> <name> 00 <data>
    '''
    def __init__(self, fname):
        self.fname = fname
        self.last = False

    def prepare_output(self, sprite_num):
        if not os.access(self.fname, os.R_OK):
            raise generic.ScriptError("File does not exist.", self.fname)
        size = os.path.getsize(self.fname)
        if size == 0:
            raise generic.ScriptError("Expected a sound file with non-zero length.", self.fname)
        if size > 0x10000:
            raise generic.ScriptError("Sound file too big (max 64KB).", self.fname)

    def write(self, file):
        file.print_named_filedata(self.fname)
        if self.last: file.newline()

class ImportSound(base_action.BaseAction):
    """
    Import a sound from another grf::

        <sprite-number> * <length> FE 00 <grfid> <number>

    @ivar grfid: ID of the other grf.
    @type grfid: C{int}

    @ivar number: Sound number to load.
    @type number: C{int}
    """
    def __init__(self, grfid, number):
        self.grfid = grfid
        self.number = number
        self.last = False

    def write(self, file):
        file.start_sprite(8)
        file.print_bytex(0xfe)
        file.print_bytex(0)
        file.print_dwordx(self.grfid)
        file.print_wordx(self.number)
        file.end_sprite()
        if self.last: file.newline()

registered_sounds = {}
SOUND_OFFSET = 73 # No of original sounds

def add_sound(args):
    if args not in registered_sounds:
        registered_sounds[args] = len(registered_sounds)
    return registered_sounds[args] + SOUND_OFFSET

def get_sound_actions():
    """
    Get a list of actions that actually includes all sounds in the output file.
    """
    if not registered_sounds:
        return []

    action_list = []
    action_list.append(Action11(len(registered_sounds)))
    volume_list = []

    for sound, i in sorted(registered_sounds.iteritems(), key=itemgetter(1)):
        if len(sound) == 3:
            action_list.append(ImportSound(sound[0], sound[1]))
        else:
            action_list.append(LoadBinaryFile(sound[0]))
        if sound[-1] != 100:
            volume_list.append( (i + SOUND_OFFSET, int(sound[-1] * 128 / 100)) )

    if volume_list:
        action_list.extend(action0.get_volume_actions(volume_list))

    return action_list

