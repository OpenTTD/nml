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

from .base_expression import ConstantNumeric, Expression, Type
from .parameter import parse_string_to_dword

storage_op_info = {
    "STORE_PERM": {"store": True, "perm": True, "grfid": False, "max": 0xFF, "reserved": ()},
    "STORE_TEMP": {"store": True, "perm": False, "grfid": False, "max": 0x10F, "reserved": range(0x80, 0xFF + 1)},
    "LOAD_PERM": {"store": False, "perm": True, "grfid": True, "max": 0xFF, "reserved": ()},
    "LOAD_TEMP": {"store": False, "perm": False, "grfid": False, "max": 0xFF, "reserved": range(0x80, 0xFF + 1)},
}


class StorageOp(Expression):
    """
    Class for reading/writing to (temporary or permanent) storage

    @ivar name: Name of the called storage function
    @type name: C{str}

    @ivar info: Dictionary containting information about the operation to perform
    @type info: C{dict}

    @ivar value: Value to store, or C{None} for loading operations
    @type value: L{Expression}

    @ivar register: Register to access
    @type register: L{Expression}

    @ivar grfid: GRFID of the register to access
    @type grfid: L{Expression}

    """

    def __init__(self, name, args, pos=None):
        Expression.__init__(self, pos)
        self.name = name
        assert name in storage_op_info
        self.info = storage_op_info[name]

        arg_len = (2,) if self.info["store"] else (1,)
        if self.info["grfid"]:
            arg_len += (arg_len[0] + 1,)
        if len(args) not in arg_len:
            argstr = "{:d}".format(arg_len[0]) if len(arg_len) == 1 else "{}..{}".format(arg_len[0], arg_len[1])
            raise generic.ScriptError(
                "{} requires {} argument(s), encountered {:d}".format(name, argstr, len(args)), pos
            )

        i = 0
        if self.info["store"]:
            self.value = args[i]
            i += 1
        else:
            self.value = None

        self.register = args[i]
        i += 1

        if i < len(args):
            self.grfid = args[i]
            assert self.info["grfid"]
        else:
            self.grfid = None

    def debug_print(self, indentation):
        generic.print_dbg(indentation, self.name)
        generic.print_dbg(indentation + 2, "Register:")
        self.register.debug_print(indentation + 4)
        if self.value is not None:
            generic.print_dbg(indentation + 2, "Value:")
            self.value.debug_print(indentation + 4)
        if self.grfid is not None:
            generic.print_dbg(indentation + 2, "GRFID:")
            self.grfid.debug_print(indentation + 4)

    def __str__(self):
        args = []
        if self.value is not None:
            args.append(str(self.value))
        args.append(str(self.register))
        if self.grfid is not None:
            args.append(str(self.grfid))
        return "{}({})".format(self.name, ", ".join(args))

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        args = []
        if self.value is not None:
            value = self.value.reduce(id_dicts)
            if value.type() != Type.INTEGER:
                if value.type() == Type.SPRITEGROUP_REF:
                    raise generic.ProcCallSyntaxError(value.name, value.pos)
                raise generic.ScriptError("Value to store must be an integer.", value.pos)
            args.append(value)

        register = self.register.reduce(id_dicts)
        if register.type() != Type.INTEGER:
            if register.type() == Type.SPRITEGROUP_REF:
                raise generic.ProcCallSyntaxError(register.name, register.pos)
            raise generic.ScriptError("Register to access must be an integer.", register.pos)
        if isinstance(register, ConstantNumeric) and register.value > self.info["max"]:
            raise generic.ScriptError("Maximum register for {} is {:d}".format(self.name, self.info["max"]), self.pos)
        if isinstance(register, ConstantNumeric) and register.value in self.info["reserved"]:
            raise generic.ScriptError(
                "Temporary registers from 128 to 255 are reserved for NML's internal calculations.", self.pos
            )
        args.append(register)

        if self.grfid is not None:
            grfid = self.grfid.reduce(id_dicts)
            # Test validity
            parse_string_to_dword(grfid)
            args.append(grfid)

        return StorageOp(self.name, args, self.pos)

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        if raise_error:
            raise generic.ScriptError("{}() may only be used inside switch-blocks".format(self.name), self.pos)
        return False

    def collect_references(self):
        return self.register.collect_references() + (self.value.collect_references() if self.value is not None else [])

    def is_read_only(self):
        assert self.info["store"] == (self.value is not None)
        return (not self.info["store"]) and self.register.is_read_only()
