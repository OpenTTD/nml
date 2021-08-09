/* NML is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NML is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with NML; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

/**
 * @file
 * Cython accelerator module.
 *
 * Loaded by lz77.py if available, to replace the universal python code if possible.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

/**
 * Resizeable buffer/array.
 */
typedef struct {
    char *buf;     ///< Plain data.
    int used;      ///< Number of bytes used.
    int allocated; ///< Number of bytes allocated.
} buffer_t;

/**
 * Append a byte to a buffer.
 * If the buffer is too small, it is enlarged.
 * @param data Buffer.
 * @param b    Byte to add.
 */
static inline void append_byte(buffer_t *data, char b)
{
    if (data->used + 1 > data->allocated) {
        data->allocated += 0x10000;
        data->buf = realloc(data->buf, data->allocated);
    }
    data->buf[data->used++] = b;
}

/**
 * Append a byte array to a buffer.
 * If the buffer is too small, it is enlarged.
 * @param data Buffer.
 * @param b    Data to add.
 * @param l    Size of \a b.
 */
static inline void append_bytes(buffer_t *data, const char *b, int l)
{
    if (data->used + l > data->allocated) {
        data->allocated = (data->used + l + 0xFFFF) & ~0xFFFF;
        data->buf = realloc(data->buf, data->allocated);
    }
    memcpy(data->buf + data->used, b, l);
    data->used += l;
}

/**
 * Locate a byte sequence in a buffer.
 * @param pat_data   Pattern to look for.
 * @param pat_size   Size of \a pat_data.
 * @param data       Data to search in.
 * @param data__size Size of \a data.
 * @return Offset of first occurence, or -1 if no match.
 */
static inline int find(const char *pat_data, int pat_size, const char *data, int data_size)
{
    int i;
    for (i = 0; i + pat_size <= data_size; ++i) {
        /* Apparently this loop is optimised quite well by gcc.
         * Usage of __builtin_bcmp performed terrible, since I didn't manage to get it inlined.
         * It it worth noting though, that pat_size is very small (<= 16). */
        int j = 0;
        while (j < pat_size && pat_data[j] == data[i + j]) ++j;
        if (j == pat_size) return i;
    }
    return -1;
}

/**
 * GRF compression algorithm.
 * @param input_data Uncompressed data.
 * @param input_size Size of \a input_data.
 * @param output     Compressed data.
 */
static void encode(const char *input_data, int input_size, buffer_t *output)
{
    char literal[0x80];
    int literal_size = 0;
    
    int position = 0;
    while (position < input_size) {
        int start_pos = position - (1 << 11) + 1;
        if (start_pos < 0) start_pos = 0;

        /* Loop through the lookahead buffer. */
        int max_look = input_size - position + 1;
        if (max_look > 16) max_look = 16;

        int overlap_pos = 0;
        int overlap_len = 0;
        int i;
        for (i = 3; i < max_look; ++i) {
            /* Find the pattern match in the window. */
            int result = find(input_data + position, i, input_data + start_pos, position - start_pos);
            /* If match failed, we've found the longest. */
            if (result < 0) break;

            overlap_pos = position - start_pos - result;
            overlap_len = i;
            start_pos += result;
        }

        if (overlap_len > 0) {
            if (literal_size > 0) {
                append_byte(output, literal_size);
                append_bytes(output, literal, literal_size);
                literal_size = 0;
            }
            int val = 0x80 | (16 - overlap_len) << 3 | overlap_pos >> 8;
            append_byte(output, val);
            append_byte(output, overlap_pos & 0xFF);
            position += overlap_len;
        } else {
            literal[literal_size++] = input_data[position];
            if (literal_size == sizeof(literal)) {
                append_byte(output, 0);
                append_bytes(output, literal, literal_size);
                literal_size = 0;
            }
            position += 1;
        }
    }
    
    if (literal_size > 0) {
        append_byte(output, literal_size);
        append_bytes(output, literal, literal_size);
        literal_size = 0;
    }
}

/**
 * Interface method to Python.
 *
 * @param self Unused.
 * @param args Uncompressed data as "str", "bytes", "bytearray", or anything providing the buffer interface.
 * @return Compressed data as "bytes".
 */
static PyObject *lz77_encode(PyObject *self, PyObject *args)
{
    PyObject *result = NULL;

    Py_buffer input;
    if (PyArg_ParseTuple(args, "s*", &input) && input.buf) {
        buffer_t output = {0};

        Py_BEGIN_ALLOW_THREADS
        encode((const char*)input.buf, input.len, &output);
        Py_END_ALLOW_THREADS

        PyBuffer_Release(&input);
        result = Py_BuildValue("y#", output.buf, output.used);
        free(output.buf);
    }

    return result;
}

/**
 * Function table.
 */
static PyMethodDef lz77Methods[] = {
    {"encode", lz77_encode, METH_VARARGS, "GRF compression algorithm"},
    {NULL, NULL, 0, NULL}
};

/**
 * Module table.
 */
static struct PyModuleDef lz77module = {
   PyModuleDef_HEAD_INIT,
   "nml_lz77", NULL, -1,
   lz77Methods
};

/**
 * Module intialisation.
 * Called by Python upon import.
 */
PyMODINIT_FUNC
PyInit_nml_lz77(void)
{
    return PyModule_Create(&lz77module);
}
