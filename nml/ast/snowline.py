import datetime
from nml import generic, expression, nmlop
from nml.actions import action0

class Snowline(object):
    """
    Snowline curve throughout the year.

    @ivar type: Type of snowline.
    @type type: C{str}

    @ivar date_heights: Height of the snow line at given days in the year.
    @type date_heights: C{list} of L{Assignment}

    @ivar pos: Position of the data in the original file.
    @type pos: L{Position}
    """
    def __init__(self, line_type, height_data, pos):
        if line_type.value not in ('equal', 'linear'):
            raise generic.ScriptError('Unknown type of snow line (only "equal" and "linear" are supported)', line_type.pos)
        self.type = line_type.value
        self.date_heights = height_data
        self.pos = pos

    def register_names(self):
        pass

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Snowline (type=%s)' % self.type
        for dh in self.date_heights:
            dh.debug_print(indentation + 2)

    def __str__(self):
        return 'snowline (%s) {\n\t%s\n}\n' % (str(self.type), '\n\t'.join([str(x) for x in self.date_heights]))

    def get_action_list(self):
        return action0.get_snowlinetable_action(compute_table(self))


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
        doy = dh.name.reduce()
        if not isinstance(doy, expression.ConstantNumeric):
            raise generic.ScriptError('Day of year is not a compile-time constant', doy.pos)
        height = dh.value.reduce()
        if snowline.type != 'equal' and not isinstance(height, expression.ConstantNumeric):
            raise generic.ScriptError('Height is not a compile-time constant', height.pos)

        if doy.value < 1 or doy.value > 365:
            raise generic.ScriptError('Day of the year must be between 1 and 365', doy.pos)
        if isinstance(height, expression.ConstantNumeric) and (height.value < 2 or height.value > 29):
            raise generic.ScriptError('Height must be between 2 and 29', height.pos)

        day_table[doy.value - 1] = height

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

        if snowline.type == 'equal':
            for day in range(start + 1, unwrapped_end):
                if day >= 365: day -= 365
                day_table[day] = startvalue
        else:
            assert snowline.type == 'linear'

            if start != end:
                dhd = float(endvalue.value - startvalue.value) / float(unwrapped_end - start)
            else:
                assert startvalue.value == endvalue.value
                dhd = 0

            for day in range(start + 1, unwrapped_end):
                uday = day
                if uday >= 365: uday -= 365
                height = startvalue.value + int(round(dhd * (day - start)))
                day_table[uday] = expression.ConstantNumeric(height)


        if end == first_point: # All days done
            break

        start = end

    table = [None] * (12*32)
    for dy in range(365):
        today = datetime.date.fromordinal(dy + 1)
        if day_table[dy]:
            expr = expression.BinOp(nmlop.MUL, day_table[dy], expression.ConstantNumeric(8)).reduce()
        else:
            expr = None
        table[(today.month - 1) * 32 + today.day - 1] = expr

    for idx, d in enumerate(table):
        if d is None:
            table[idx] = table[idx - 1]
    #Second loop is needed because we need make sure the first item is also set.
    for idx, d in enumerate(table):
        if d is None:
            table[idx] = table[idx - 1]


    return table

