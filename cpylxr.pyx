cdef extern from "clxr.c":
    pass

cdef extern from "clxr.h":
    void h_in_C(int, unsigned char *, unsigned char *, int, unsigned char *)

import numpy as np

def h(map_size_bits, byte_map, src):
    if not byte_map.flags['C_CONTIGUOUS']:
        byte_map = np.ascontiguousarray(byte_map)  # Makes a contiguous copy of the numpy array.
    cdef unsigned char[::1] bytemap_memview = byte_map

    if not src.flags['C_CONTIGUOUS']:
        src = np.ascontiguousarray(src)  # Makes a contiguous copy of the numpy array.
    cdef unsigned char[::1] src_memview = src

    hash_arr = np.zeros(32, dtype=np.uint8)
    cdef unsigned char[::1] hash_memview = hash_arr

    if src_memview.shape[0] != 0:
        h_in_C(map_size_bits, &bytemap_memview[0], &src_memview[0], src_memview.shape[0], &hash_memview[0])
    else:
        # HACK, getting index out of bounds for &src_memview[0] so pas in the one for hash_memview
        h_in_C(map_size_bits, &bytemap_memview[0], &hash_memview[0], src_memview.shape[0], &hash_memview[0])

    return hash_arr
