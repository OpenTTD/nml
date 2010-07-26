class Assignment(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'Assignment, name = ', self.name
        self.value.debug_print(indentation + 2)
