try:
    from __pypy__.builders import StringBuilder
    class StringIO:
        """
        Mimic basic StringIO behavior, but then faster.
        """
        def __init__(self):
            self.builder = StringBuilder()
            self.write = self.builder.append
        def getvalue(self):
            return self.builder.build()
except ImportError:
    from io import StringIO

__all__ = [
    "StringIO",
]
