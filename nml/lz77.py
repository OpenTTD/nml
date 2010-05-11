# Boyer-Moore-Horspool fast string search.
class BMH:
    def pattern(self, data):
        self.data = data
        self.skip = 256 * [len(self.data)]
        for k in range(len(self.data) - 1): self.skip[data[k]] = len(self.data) - k - 1
    def find(self, text):
        n = len(text)
        if len(self.data) > n: return -1
        k = len(self.data) - 1
        while k < n:
            j = len(self.data) - 1
            i = k
            while j >= 0 and text[i] == self.data[j]:
                j -= 1
                i -= 1
            if j == -1: return i + 1
            k += self.skip[text[k]]
        return -1

class LZ77:
    def __init__(self, data):
        self.position = 0
        self.stream = data
        self.remaining = len(self.stream)
        self.search = BMH()
    def Encode(self):
        output = []
        literal_bytes = []
        while self.position < len(self.stream):
            overlap_len = 0
            self.window = self.stream[max(0, self.position - (1 << 11) + 1) : self.position]
            # Loop through the lookahead buffer.
            for i in range(3, min(len(self.stream) - self.position + 1, 16)):
                # Set pattern to find the longest match.
                self.search.pattern(self.stream[self.position:self.position+i])
                # Find the pattern match in the window.
                result = self.search.find(self.window)
                # If match failed, we've found the longest.
                if result < 0: break
                p = len(self.window) - result
                overlap_len = i
            if overlap_len > 0:
                if len(literal_bytes) > 0:
                    output.append(len(literal_bytes))
                    output += literal_bytes
                    literal_bytes = []
                output.append(((-overlap_len) << 3) & 0xFF | (p >> 8))
                output.append(p & 0xFF)
                self.position += overlap_len
            else:
                literal_bytes.append(self.stream[self.position])
                if len(literal_bytes) == 0x80:
                    output.append(0)
                    output += literal_bytes
                    literal_bytes = []
                self.position += 1
        if len(literal_bytes) > 0:
            output.append(len(literal_bytes))
            output += literal_bytes
        return output

