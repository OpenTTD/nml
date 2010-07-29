"""
Action 11 support classes (sounds).
"""
import os
from nml import generic, expression
from nml.actions import base_action

class Action11(base_action.BaseAction):
    def __init__(self, sounds):
        self.sounds = sounds
        self.sounds[-1].last = True

    def prepare_output(self):
        if len(self.sounds) == 0:
            raise generic.ScriptError('Expected at least one sound.')
        for sound in self.sounds: sound.prepare_output()

    def write(self, file):
        file.start_sprite(3)
        file.print_bytex(0x11)
        file.print_word(len(self.sounds))
        file.end_sprite()

    def pre_process(self):
        pass

    def get_action_list(self):
        return [self] + self.sounds

    def debug_print(self, indentation):
        print indentation*' ' + 'Sounds:'
        for sound in self.sounds: sound.debug_print(indentation + 2)


class LoadBinaryFile(object):
    '''
    <sprite-number> * <length> FF <name-len> <name> 00 <data>
    '''
    def __init__(self, fname, pos):
        self.fname = fname
        self.last = False
        self.pos = pos

    def prepare_output(self):
        if not os.access(self.fname.value, os.R_OK):
            raise generic.ScriptError('File "%s" does not exist.' % self.fname.value, self.pos)
        size = os.path.getsize(self.fname.value)
        if size == 0:
            raise generic.ScriptError("Expected a sound file with non-zero length.", self.pos)
        if size > 0x10000:
            raise generic.ScriptError("Sound file too big (max 64KB).", self.pos)

    def debug_print(self, indentation):
        name = os.path.split(self.fname.value)[1]
        if os.path.isfile(self.fname.value):
            size = str(os.path.getsize(self.fname.value))
        else:
            size = '???'
        print indentation*' ' + 'load binary file %r (filename %r), %s bytes' % (self.fname.value, name, size)

    def write(self, file):
        file.print_named_filedata(self.fname.value)
        if self.last: file.newline()

class ImportSound(object):
    """
    Import a sound from another grf::

        <sprite-number> * <length> FE 00 <grfid> <number>

    @ivar grfid: ID of the other grf.
    @type grfid: C{int}

    @ivar number: Sound number to load.
    @type number: C{int}
    """
    def __init__(self, grfid, number, pos):
        grfid = grfid.reduce_constant()
        if not isinstance(grfid, expression.ConstantNumeric):
            raise generic.ScriptError("grf id of the imported sound is not a number.", grfid.pos)
        self.grfid = grfid.value
        self.pos = pos

        number = number.reduce_constant()
        if not isinstance(number, expression.ConstantNumeric):
            raise generic.ScriptError("sound number of the imported sound is not a number.", number.pos)
        self.number = number.value
        self.last = False

    def prepare_output(self):
        pass

    def debug_print(self, indentation):
        value = self.grfid
        if -0x80000000 < value < 0: value += 0x100000000
        print indentation*' ' + 'import sound %d from NewGRF %s' % (self.number, hex(value))

    def write(self, file):
        file.start_sprite(8)
        file.print_bytex(0xfe)
        file.print_bytex(0)
        file.print_dwordx(self.grfid)
        file.print_wordx(self.number)
        file.end_sprite()
        if self.last: file.newline()
