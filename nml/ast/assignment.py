class Assignment(object):
    """
    Simple storage container for a name / value pair.
    This class does not enforce any type information.
    Create a subclass to do this, or hard-code it in the parser.

    @ivar name: Name of the parameter / property / whatever to be set.
    @type name: Anything

    @ivar value: Value to assign to <name>
    @type value: Anything

    @ivar pos: Position information of the assignment
    @type pos: L{Position}
    """
    def __init__(self, name, value, pos):
        self.name = name
        self.value = value
        self.pos = pos

    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment'
        print (indentation+2)*' ' + 'Name:'
        self.name.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Value:'
        self.value.debug_print(indentation + 4)

    def __str__(self):
        return "%s: %s;" % (str(self.name), str(self.value))

class Range(object):
    """
    Storage container for a range of values (inclusive). This Contains
    a minimum value and optionally also a maximum value. If the maximum
    values is omitted, the minimum is also used as maximum.

    @ivar min: The minimum value of this range.
    @type min: L{Expression}

    @ivar max: THe maximum value of this range.
    @type max: L{Expression} or C{None}
    """
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __str__(self):
        if self.max is None:
            return str(self.min)
        return "%s .. %s" % (str(self.min), str(self.max))

