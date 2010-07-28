import datetime
from nml import generic, expression
from nml.actions import action0

class Snowline(object):
    """
    Snowline curve throughout the year.

    @ivar type: Type of snowline.
    @type type: L{SnowlineType}

    @ivar date_heights: Height of the snow line at given days in the year.
    @type date_heights: C{list} of L{SnowDateHeight}

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """
    def __init__(self, height_data, pos):
        self.date_heights = height_data[0]
        if len(height_data[1]) > 0:
            self.type = height_data[1][0]
            for st in height_data[1][1:]:
                generic.print_warning('Snowline type "%s" ignored' % st.type, st.pos)
        else:
            self.type = SnowlineType('equal', None)
        self.pos = pos

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Snowline (type=%s)' % self.type.type
        for dh in self.date_heights:
            dh.debug_print(indentation + 2)

    def get_action_list(self):
        return action0.get_snowlinetable_action(compute_table(self))

class SnowlineType(object):
    """
    Type of snowline.

    @ivar type: Type of the snowline. Allowed values
                 - equal:  The same as the day before unless specified otherwise
                 - linear: Linear interpolation of the height between heights at two days given.
    @type type: C{str}

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """
    def __init__(self, type, pos):
        self.type = type.value
        self.pos = pos

        if self.type not in ('equal', 'linear'):
            raise generic.ScriptError('Unknown type of snow line (only "equal" and "linear" are supported)', self.pos)


class SnowDateHeight(object):
    """
    Snowline height at a certain date in the year.

    @ivar day_of_year: Day of the year, between 1 and 355.
    @type day_of_year: L{Expression}

    @ivar height: Height of the snow line at the given day.
    @type height: L{Expression}

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """
    def __init__(self, day_of_year, height, pos):
        self.day_of_year = day_of_year
        self.height = height
        self.pos = pos

    def debug_print(self, indentation):
        print " " * indentation + "day: " + str(self.day_of_year) + ", height: " + str(self.height)



def compute_table(snowline):
    """
    Compute the table with snowline height for each day of the year.

    @param snowline: Snowline definition.
    @type  snowline: L{Snowline}

    @return: Table of 12*32 entries with snowline heights.
    @rtype:  C{str}
    """
    day_table = [None]*365 # Height at each day, starting at day 0
    for dh in snowline.date_heights:
        doy = dh.day_of_year.reduce()
        if not isinstance(doy, expression.ConstantNumeric):
            raise generic.ScriptError('Day of year is not a compile-time constant', dh.pos)
        height = dh.height.reduce()
        if not isinstance(height, expression.ConstantNumeric):
            raise generic.ScriptError('Height is not a compile-time constant', dh.pos)

        if doy.value < 1 or doy.value > 365:
            raise generic.ScriptError('Day of the year must be between 1 and 365', dh.pos)
        if height.value < 2 or height.value > 29:
            raise generic.ScriptError('Height must be between 2 and 29', dh.pos)

        day_table[doy.value - 1] = height.value

    # Find first specified point.
    start = 0
    while start < 365 and day_table[start] is None:
        start = start + 1
    if start == 365:
        raise generic.ScriptError('No heights given for the snowline table', snowline.pos)

    first_point = start
    while True:
        # Find second point from start
        end = start + 1
        if end == 365:
            end = 0

        while end != first_point and day_table[end] is None:
            end = end + 1
            if end == 365:
                end = 0

        # Fill the days between start and end (exclusive both border values)
        startvalue = day_table[start]
        endvalue   = day_table[end]
        unwrapped_end = end
        if end < start: unwrapped_end += 365

        if snowline.type.type == 'equal':
            for day in range(start + 1, unwrapped_end):
                if day >= 365: day -= 365
                day_table[day] = startvalue
        else:
            assert snowline.type.type == 'linear'

            dhd = float(endvalue - startvalue) / float(unwrapped_end - start)
            for day in range(start + 1, unwrapped_end):
                uday = day
                if uday >= 365: uday -= 365
                height = startvalue + int(round(dhd * (day - start)))
                day_table[uday] = height


        if end == first_point: # All days done
            break

        start = end

    table = [None] * (12*32)
    for dy in range(365):
        today = datetime.date.fromordinal(dy + 1)
        table[(today.month - 1) * 32 + today.day - 1] = day_table[dy]

    for idx, d in enumerate(table):
        if d is None:
            table[idx] = table[idx - 1]

    return ''.join(chr(d*8) for d in table)

