"""
Action 11 support classes (sounds).
"""
import os
from nml import expression

class Action11(object):
    def __init__(self, sounds):
        self.sounds = sounds

    def prepare_output(self):
        if len(self.sounds) == 0:
            raise ScriptError('Expected at least one sound.')
        for sound in self.sounds: sound.prepare_output()

    def write(self, file):
        file.print_sprite_size(3)
        file.print_byte(0x11)
        file.print_word(len(self.sounds))
        file.newline()

    def skip_action7(self):
        return True

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

    def get_action_list(self):
        return [self] + self.sounds

    def debug_print(self, indentation):
        print indentation*' ' + 'Sounds:'
        for sound in self.sounds: sound.debug_print(indentation + 2)


class LoadBinaryFile(object):
    '''
    <sprite-number> * <length> FF <name-len> <name> 00 <data>
    '''
    def __init__(self, fname):
        self.fname = fname

    def prepare_output(self):
        if not os.path.isfile(self.fname):
            raise ScriptError('File "%s" does not exist.')
        size = os.path.getsize(self.fname)
        if size == 0:
            raise ScriptError("Expected a sound file with non-zero length.")
        if size > 0x10000:
            raise ScriptError("Sound file too big (max 64KB).")

    def debug_print(self, indentation):
        name = os.path.split(self.fname)[1]
        if os.path.isfile(self.fname):
            size = str(os.path.getsize(self.fname))
        else:
            size = '???'
        print indentation*' ' + 'load binary file %r (filename %r), %s bytes' % (self.fname, name, size)

    def write(self, file):
        file.print_named_filedata(self.fname)
        file.newline()

class ImportSound(object):
    """
    Import a sound from another grf::

        <sprite-number> * <length> FE 00 <grfid> <number>

    @ivar grfid: ID of the other grf.
    @type grfid: C{int}

    @ivar number: Sound number to load.
    @type number: C{int}
    """
    def __init__(self, grfid, number):
        grfid = expression.reduce_constant(grfid)
        if not isinstance(grfid, expression.ConstantNumeric):
            raise ScriptError("grf id of the imported sound is not a number.")
        self.grfid = grfid.value

        number = expression.reduce_constant(number)
        if not isinstance(number, expression.ConstantNumeric):
            raise ScriptError("sound number of the imported sound is not a number.")
        self.number = number.value

    def prepare_output(self):
        pass

    def debug_print(self, indentation):
        value = self.grfid
        if -0x80000000 < value < 0: value += 0x100000000
        print indentation*' ' + 'import sound %d from NewGRF %s' % (self.number, hex(value))

    def write(self, file):
        file.print_sprite_size(8)
        file.print_bytex(0xfe)
        file.print_bytex(0)
        file.print_dwordx(self.grfid)
        file.print_wordx(self.number)
        file.newline()
