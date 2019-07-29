import datetime
import numpy as np
import os
from dataclasses import dataclass, field


u64 = np.uint64


@dataclass
class LXR:
    map_size_bits: int = 30
    passes: int = 5
    seed: bytes = b"\xfa\xfa\xec\xec\xfa\xfa\xec\xec"
    hash_size: u64 = 256

    seed_int: u64 = field(init=False)
    map_size: u64 = field(init=False)
    byte_map: np.ndarray = field(init=False)

    def __post_init__(self):
        if self.map_size_bits < 8 or 34 < self.map_size_bits:
            raise ValueError("Map size must be between 8 and 34 bits")
        self.seed_int = u64(int(self.seed.hex(), 16))
        self.map_size = u64(1) << u64(self.map_size_bits)
        self.byte_map = np.zeros(self.map_size, dtype='uint64')
        self.hash_size = u64((self.hash_size + 7) / 8)
        self._read_table()

    def h(self, src: bytes) -> bytes:
        h = np.zeros(self.hash_size, dtype='uint64')
        a = u64(self.seed_int)
        s1, s2, s3 = u64(0), u64(0), u64(0)
        mask = u64(self.map_size - 1)

        index = u64(0)
        # Fast spin to prevent caching state
        for _ in src:
            if index >= self.hash_size:
                index = u64(0)
            a = index << u64(1) ^ a << u64(7) ^ a >> u64(5)
            s1 = s1 << u64(9) ^ s1 >> u64(3) ^ a
            h[index] = s1 ^ a
            a, s1, s2, s3 = s3, a, s1, s2
            index += u64(1)

        _0 = u64(0)
        _1 = u64(1)
        _3 = u64(3)
        _4 = u64(4)
        _5 = u64(5)
        _6 = u64(6)
        _7 = u64(7)
        _8 = u64(8)
        _9 = u64(9)
        _10 = u64(10)
        _11 = u64(11)
        _13 = u64(13)
        _15 = u64(15)
        _17 = u64(17)
        _23 = u64(23)
        _27 = u64(27)

        index = u64(0)
        for bit in src:
            bit = u64(bit)
            if index >= self.hash_size:
                index = _0
            # Shifts are not random.  They are selected to ensure that
            # Prior bytes pulled from the ByteMap contribute to the
            # next access of the ByteMap, either by contributing to
            # the lower bits of the index, or in the upper bits that
            # move the access further in the map.

            # We also pay attention not only to where the ByteMap bits
            # are applied, but what bits we use in the indexing of the ByteMap

            # Tests run against this set of shifts show that the
            # bytes pulled from the ByteMap are evenly distributed
            # over possible byte values (0-255) and indexes into
            # the ByteMap are also evenly distributed, and the
            # deltas between bytes provided map to a curve expected
            # (fewer maximum and minimum deltas, and most deltas around zero.
            s1 = s1 << _9 ^ s1 >> _1 ^ a ^ self.byte_map[(a >> _5 ^ bit) & mask] << _3
            s1 = s1 << _5 ^ s1 >> _3 ^ self.byte_map[(s1 ^ bit) & mask] << _7
            s1 = s1 << _7 ^ s1 >> _7 ^ self.byte_map[(a ^ s1 >> _7) & mask] << _5
            s1 = s1 << _11 ^ s1 >> _5 ^ self.byte_map[(bit ^ a >> _11 ^ s1) & mask] << _27

            h[index] = s1 ^ a ^ h[index] << _7 ^ h[index] >> _13

            a = a << _17 ^ a >> _5 ^ s1 ^ self.byte_map[(a ^ s1 >> _27 ^ bit) & mask] << _3
            a = a << _13 ^ a >> _3 ^ self.byte_map[(a ^ s1) & mask] << _7
            a = a << _15 ^ a >> _7 ^ self.byte_map[(a >> _7 ^ s1) & mask] << _11
            a = a << _9 ^ a >> _11 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _3

            s1 = s1 << _7 ^ s1 >> _27 ^ a ^ self.byte_map[(a >> _3) & mask] << _13
            s1 = s1 << _3 ^ s1 >> _13 ^ self.byte_map[(s1 ^ bit) & mask] << _11
            s1 = s1 << _8 ^ s1 >> _11 ^ self.byte_map[(a ^ s1 >> _11) & mask] << _9
            s1 = s1 << _6 ^ s1 >> _9 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _3

            a = a << _23 ^ a >> _3 ^ s1 ^ self.byte_map[(a ^ bit ^ s1 >> _3) & mask] << _7
            a = a << _17 ^ a >> _7 ^ self.byte_map[(a ^ s1 >> _3) & mask] << _5
            a = a << _13 ^ a >> _5 ^ self.byte_map[(a >> _5 ^ s1) & mask] << _1
            a = a << _11 ^ a >> _1 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _7

            s1 = s1 << _5 ^ s1 >> _3 ^ a ^ self.byte_map[(a >> _7 ^ s1 >> _3) & mask] << _6
            s1 = s1 << _8 ^ s1 >> _6 ^ self.byte_map[(s1 ^ bit) & mask] << _11
            s1 = s1 << _11 ^ s1 >> _11 ^ self.byte_map[(a ^ s1 >> _11) & mask] << _5
            s1 = s1 << _7 ^ s1 >> _5 ^ self.byte_map[(bit ^ a >> _7 ^ a ^ s1) & mask] << _17

            s2 = s2 << _3 ^ s2 >> _17 ^ s1 ^ self.byte_map[(a ^ s2 >> _5 ^ bit) & mask] << _13
            s2 = s2 << _6 ^ s2 >> _13 ^ self.byte_map[s2 & mask] << _11
            s2 = s2 << _11 ^ s2 >> _11 ^ self.byte_map[(a ^ s1 ^ s2 >> _11) & mask] << _23
            s2 = s2 << _4 ^ s2 >> _23 ^ self.byte_map[(bit ^ a >> _8 ^ a ^ s2 >> _10) & mask] << _1

            s1 = s2 << _3 ^ s2 >> _1 ^ h[index] ^ bit
            a = a << _9 ^ a >> _7 ^ s1 >> _1 ^ self.byte_map[(s2 >> _1 ^ h[index]) & mask] << _5

            s1, s2, s3 = s3, s1, s2
            index += _1

        # Reduction pass
        # Done by iterating over hs[] to produce the bytes[] hash
        #
        # At this point, we have HBits of state in hs.  We need to reduce them down to a byte,
        # And we do so by doing a bit more bitwise math, and mapping the values through our byte map.

        hash_bytes = bytearray(self.hash_size)
        # Roll over all the hs (one int64 value for every byte in the resulting hash) and reduce them to byte values
        for i, bit in enumerate(h):
            # Duplicated from above to reduce function call overhead
            s1 = s1 << _9 ^ s1 >> _1 ^ a ^ self.byte_map[(a >> _5 ^ bit) & mask] << _3
            s1 = s1 << _5 ^ s1 >> _3 ^ self.byte_map[(s1 ^ bit) & mask] << _7
            s1 = s1 << _7 ^ s1 >> _7 ^ self.byte_map[(a ^ s1 >> _7) & mask] << _5
            s1 = s1 << _11 ^ s1 >> _5 ^ self.byte_map[(bit ^ a >> _11 ^ s1) & mask] << _27

            h[i] = s1 ^ a ^ h[i] << _7 ^ h[i] >> _13

            a = a << _17 ^ a >> _5 ^ s1 ^ self.byte_map[(a ^ s1 >> _27 ^ bit) & mask] << _3
            a = a << _13 ^ a >> _3 ^ self.byte_map[(a ^ s1) & mask] << _7
            a = a << _15 ^ a >> _7 ^ self.byte_map[(a >> _7 ^ s1) & mask] << _11
            a = a << _9 ^ a >> _11 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _3

            s1 = s1 << _7 ^ s1 >> _27 ^ a ^ self.byte_map[(a >> _3) & mask] << _13
            s1 = s1 << _3 ^ s1 >> _13 ^ self.byte_map[(s1 ^ bit) & mask] << _11
            s1 = s1 << _8 ^ s1 >> _11 ^ self.byte_map[(a ^ s1 >> _11) & mask] << _9
            s1 = s1 << _6 ^ s1 >> _9 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _3

            a = a << _23 ^ a >> _3 ^ s1 ^ self.byte_map[(a ^ bit ^ s1 >> _3) & mask] << _7
            a = a << _17 ^ a >> _7 ^ self.byte_map[(a ^ s1 >> _3) & mask] << _5
            a = a << _13 ^ a >> _5 ^ self.byte_map[(a >> _5 ^ s1) & mask] << _1
            a = a << _11 ^ a >> _1 ^ self.byte_map[(bit ^ a ^ s1) & mask] << _7

            s1 = s1 << _5 ^ s1 >> _3 ^ a ^ self.byte_map[(a >> _7 ^ s1 >> _3) & mask] << _6
            s1 = s1 << _8 ^ s1 >> _6 ^ self.byte_map[(s1 ^ bit) & mask] << _11
            s1 = s1 << _11 ^ s1 >> _11 ^ self.byte_map[(a ^ s1 >> _11) & mask] << _5
            s1 = s1 << _7 ^ s1 >> _5 ^ self.byte_map[(bit ^ a >> _7 ^ a ^ s1) & mask] << _17

            s2 = s2 << _3 ^ s2 >> _17 ^ s1 ^ self.byte_map[(a ^ s2 >> _5 ^ bit) & mask] << _13
            s2 = s2 << _6 ^ s2 >> _13 ^ self.byte_map[s2 & mask] << _11
            s2 = s2 << _11 ^ s2 >> _11 ^ self.byte_map[(a ^ s1 ^ s2 >> _11) & mask] << _23
            s2 = s2 << _4 ^ s2 >> _23 ^ self.byte_map[(bit ^ a >> _8 ^ a ^ s2 >> _10) & mask] << _1

            s1 = s2 << _3 ^ s2 >> _1 ^ h[i] ^ bit
            a = a << _9 ^ a >> _7 ^ s1 >> _1 ^ self.byte_map[(s2 >> _1 ^ h[i]) & mask] << _5

            s1, s2, s3 = s3, s1, s2
            hash_bytes[i] = self.byte_map[a & mask] ^ self.byte_map[h[i] & mask]

        return bytes(hash_bytes)

    def _generate_table(self):
        # Our own "random" generator that really is just used to shuffle values
        first_rand = u64(2458719153079158768)
        first_b = u64(4631534797403582785)
        first_v = u64(3523455478921636871)

        offset = self.seed_int ^ first_rand
        b = self.seed_int ^ first_b
        v = first_v
        mask = self.map_size - u64(1)

        # Fill the ByteMap with bytes ranging from 0 to 255.  As long as map_size % 256 == 0, this
        # looping and masking works just fine.
        print("Initializing the Table")
        for i in self.byte_map:
            self.byte_map[i] = u64(i)

        # Now what we want to do is just mix it all up.  Take every byte in the ByteMap list, and exchange it
        # for some other byte in the ByteMap list. Note that we do this over and over, mixing and more mixing
        # the ByteMap, but maintaining the ratio of each byte value in the ByteMap list.
        print("Shuffling the Table")
        for loop in range(self.passes):
            print(f"Pass {loop}")
            start = datetime.datetime.now()
            for iteration, i in enumerate(self.byte_map):
                # The random index used to shuffle the ByteMap is itself computed through the ByteMap table
                # in a deterministic pattern.
                offset = offset << u64(9) ^ offset >> u64(1) ^ offset >> u64(7) ^ b
                v = self.byte_map[(offset ^ b) & mask] ^ v << u64(8) ^ v >> u64(1)
                b = v << u64(7) ^ v << u64(13) ^ v << u64(33) ^ v << u64(52) ^ b << u64(9) ^ b >> u64(1)
                j = offset & mask
                self.byte_map[i], self.byte_map[j] = self.byte_map[j], self.byte_map[i]
            n = len(self.byte_map) / 1024000
            time = datetime.datetime.now() - start
            print(f" Index {n} Meg of {n} Meg -- Pass is 100% Complete (time taken: {time})")

    def _read_table(self):
        home = os.getenv("HOME")
        path = f"{home}/.lxrhash"

        if not os.path.exists(path):
            os.mkdir(path)

        filename = f"{path}/lxrhash-seed-{self.seed.hex()}-passes-{self.passes}-size-{self.map_size_bits}.dat"
        print(f"Reading ByteMap Table {filename}")
        start = datetime.datetime.now()
        found = False
        if os.path.exists(filename):
            with open(filename, "rb+") as f:
                data = f.read()
                if len(data) == self.map_size:
                    self.byte_map = np.frombuffer(data, dtype=np.uint8).astype(u64)
                    found = True

        if not found:
            print("Table not found, Generating ByteMap Table")
            self._generate_table()
            print("Writing ByteMap Table")
            with open(filename, "wb+") as f:
                f.write(self.byte_map)

        print(f"Done. Total time taken: {datetime.datetime.now() - start}")
