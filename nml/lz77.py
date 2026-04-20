# SPDX-License-Identifier: GPL-2.0-or-later

import array


def _encode(data):
    """
    GRF compression algorithm.

    @param data: Uncompressed data.
    @type  data: C{str}, C{bytearray}, C{bytes} or similar.

    @return: Compressed data.
    @rtype:  C{bytearray}
    """
    stream = data.tobytes()
    position = 0
    output = array.array("B")
    literal_bytes = array.array("B")
    stream_len = len(stream)

    while position < stream_len:
        overlap_len = 0
        start_pos = max(0, position - (1 << 11) + 1)
        # Loop through the lookahead buffer.
        for i in range(3, min(stream_len - position + 1, 16)):
            # Set pattern to find the longest match.
            pattern = stream[position : position + i]
            # Find the pattern match in the window.
            result = stream.find(pattern, start_pos, position)
            # If match failed, we've found the longest.
            if result < 0:
                break

            p = position - result
            overlap_len = i
            start_pos = result

        if overlap_len > 0:
            if len(literal_bytes) > 0:
                output.append(len(literal_bytes))
                output.extend(literal_bytes)
                literal_bytes = array.array("B")

            val = ((-overlap_len) << 3) & 0xFF | (p >> 8)
            output.append(val)
            output.append(p & 0xFF)
            position += overlap_len
        else:
            literal_bytes.append(stream[position])
            if len(literal_bytes) == 0x80:
                output.append(0)
                output.extend(literal_bytes)
                literal_bytes = array.array("B")

            position += 1

    if len(literal_bytes) > 0:
        output.append(len(literal_bytes))
        output.extend(literal_bytes)

    return output


"""
True if the encoding is provided by a native module.
Used for verbose information.
"""
is_native = False

try:
    from nml_lz77 import encode  # lgtm[py/unused-import]

    is_native = True
except ImportError:
    encode = _encode
