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
    verbose: bool = False

    seed_int: u64 = field(init=False)
    map_size: u64 = field(init=False)
    byte_map: np.ndarray = field(init=False)

    def __post_init__(self):
        if self.map_size_bits < 8 or 34 < self.map_size_bits:
            raise ValueError("Map size must be between 8 and 34 bits")
        self.seed_int = u64(int(self.seed.hex(), 16))
        self.map_size = u64(1) << u64(self.map_size_bits)
        self.byte_map = np.zeros(self.map_size, dtype="uint64")
        self.hash_size = u64((self.hash_size + 7) / 8)
        self._read_table()

    def h(self, src: bytes) -> bytes:
        h = np.zeros(self.hash_size, dtype="uint64")
        a = self.seed_int
        s1, s2, s3 = u64(0), u64(0), u64(0)
        mask = self.map_size - u64(1)

        # Cache these casted values since they're used a lot in the hashing loop
        b = self.byte_map
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
        _12 = u64(12)
        _13 = u64(13)
        _15 = u64(15)
        _16 = u64(16)
        _17 = u64(17)
        _20 = u64(20)
        _23 = u64(23)
        _27 = u64(27)

        # Fast spin to prevent caching state
        index = _0
        for v in src:
            v = u64(v)
            if index >= self.hash_size:
                index = _0
            bit = b[(a ^ v) & mask]
            a = a << _7 ^ a >> _5 ^ v << _20 ^ v << _16 ^ v ^ bit << _20 ^ bit << _12 ^ bit << _4
            s1 = s1 << _9 ^ s1 >> _3 ^ h[index]
            h[index] = s1 ^ a
            s1, s2, s3 = s3, s1, s2
            index += _1

        # Actual work to compute the hash
        index = _0
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
            s1 = s1 << _9 ^ s1 >> _1 ^ a ^ b[(a >> _5 ^ bit) & mask] << _3
            s1 = s1 << _5 ^ s1 >> _3 ^ b[(s1 ^ bit) & mask] << _7
            s1 = s1 << _7 ^ s1 >> _7 ^ b[(a ^ s1 >> _7) & mask] << _5
            s1 = s1 << _11 ^ s1 >> _5 ^ b[(bit ^ a >> _11 ^ s1) & mask] << _27

            h[index] = s1 ^ a ^ h[index] << _7 ^ h[index] >> _13

            a = a << _17 ^ a >> _5 ^ s1 ^ b[(a ^ s1 >> _27 ^ bit) & mask] << _3
            a = a << _13 ^ a >> _3 ^ b[(a ^ s1) & mask] << _7
            a = a << _15 ^ a >> _7 ^ b[(a >> _7 ^ s1) & mask] << _11
            a = a << _9 ^ a >> _11 ^ b[(bit ^ a ^ s1) & mask] << _3

            s1 = s1 << _7 ^ s1 >> _27 ^ a ^ b[(a >> _3) & mask] << _13
            s1 = s1 << _3 ^ s1 >> _13 ^ b[(s1 ^ bit) & mask] << _11
            s1 = s1 << _8 ^ s1 >> _11 ^ b[(a ^ s1 >> _11) & mask] << _9
            s1 = s1 << _6 ^ s1 >> _9 ^ b[(bit ^ a ^ s1) & mask] << _3

            a = a << _23 ^ a >> _3 ^ s1 ^ b[(a ^ bit ^ s1 >> _3) & mask] << _7
            a = a << _17 ^ a >> _7 ^ b[(a ^ s1 >> _3) & mask] << _5
            a = a << _13 ^ a >> _5 ^ b[(a >> _5 ^ s1) & mask] << _1
            a = a << _11 ^ a >> _1 ^ b[(bit ^ a ^ s1) & mask] << _7

            s1 = s1 << _5 ^ s1 >> _3 ^ a ^ b[(a >> _7 ^ s1 >> _3) & mask] << _6
            s1 = s1 << _8 ^ s1 >> _6 ^ b[(s1 ^ bit) & mask] << _11
            s1 = s1 << _11 ^ s1 >> _11 ^ b[(a ^ s1 >> _11) & mask] << _5
            s1 = s1 << _7 ^ s1 >> _5 ^ b[(bit ^ a >> _7 ^ a ^ s1) & mask] << _17

            s2 = s2 << _3 ^ s2 >> _17 ^ s1 ^ b[(a ^ s2 >> _5 ^ bit) & mask] << _13
            s2 = s2 << _6 ^ s2 >> _13 ^ b[s2 & mask] << _11
            s2 = s2 << _11 ^ s2 >> _11 ^ b[(a ^ s1 ^ s2 >> _11) & mask] << _23
            s2 = s2 << _4 ^ s2 >> _23 ^ b[(bit ^ a >> _8 ^ a ^ s2 >> _10) & mask] << _1

            s1 = s2 << _3 ^ s2 >> _1 ^ h[index] ^ bit
            a = a << _9 ^ a >> _7 ^ s1 >> _1 ^ b[(s2 >> _1 ^ h[index]) & mask] << _5

            s1, s2, s3 = s3, s1, s2
            index += _1

        # Reduction pass
        # Done by iterating over hs[] to produce the bytes[] hash
        # At this point, we have HBits of state in hs.  We need to reduce them down to a byte,
        # And we do so by doing a bit more bitwise math, and mapping the values through our byte map.
        hash_bytes = bytearray(self.hash_size)
        # Roll over all the hs (one int64 value for every byte in the resulting hash) and reduce them to byte values
        for i in range(len(h) - 1, -1, -1):
            bit = h[i]
            # Duplicated from above to reduce function call overhead
            s1 = s1 << _9 ^ s1 >> _1 ^ a ^ b[(a >> _5 ^ bit) & mask] << _3
            s1 = s1 << _5 ^ s1 >> _3 ^ b[(s1 ^ bit) & mask] << _7
            s1 = s1 << _7 ^ s1 >> _7 ^ b[(a ^ s1 >> _7) & mask] << _5
            s1 = s1 << _11 ^ s1 >> _5 ^ b[(bit ^ a >> _11 ^ s1) & mask] << _27

            h[i] = s1 ^ a ^ h[i] << _7 ^ h[i] >> _13

            a = a << _17 ^ a >> _5 ^ s1 ^ b[(a ^ s1 >> _27 ^ bit) & mask] << _3
            a = a << _13 ^ a >> _3 ^ b[(a ^ s1) & mask] << _7
            a = a << _15 ^ a >> _7 ^ b[(a >> _7 ^ s1) & mask] << _11
            a = a << _9 ^ a >> _11 ^ b[(bit ^ a ^ s1) & mask] << _3

            s1 = s1 << _7 ^ s1 >> _27 ^ a ^ b[(a >> _3) & mask] << _13
            s1 = s1 << _3 ^ s1 >> _13 ^ b[(s1 ^ bit) & mask] << _11
            s1 = s1 << _8 ^ s1 >> _11 ^ b[(a ^ s1 >> _11) & mask] << _9
            s1 = s1 << _6 ^ s1 >> _9 ^ b[(bit ^ a ^ s1) & mask] << _3

            a = a << _23 ^ a >> _3 ^ s1 ^ b[(a ^ bit ^ s1 >> _3) & mask] << _7
            a = a << _17 ^ a >> _7 ^ b[(a ^ s1 >> _3) & mask] << _5
            a = a << _13 ^ a >> _5 ^ b[(a >> _5 ^ s1) & mask] << _1
            a = a << _11 ^ a >> _1 ^ b[(bit ^ a ^ s1) & mask] << _7

            s1 = s1 << _5 ^ s1 >> _3 ^ a ^ b[(a >> _7 ^ s1 >> _3) & mask] << _6
            s1 = s1 << _8 ^ s1 >> _6 ^ b[(s1 ^ bit) & mask] << _11
            s1 = s1 << _11 ^ s1 >> _11 ^ b[(a ^ s1 >> _11) & mask] << _5
            s1 = s1 << _7 ^ s1 >> _5 ^ b[(bit ^ a >> _7 ^ a ^ s1) & mask] << _17

            s2 = s2 << _3 ^ s2 >> _17 ^ s1 ^ b[(a ^ s2 >> _5 ^ bit) & mask] << _13
            s2 = s2 << _6 ^ s2 >> _13 ^ b[s2 & mask] << _11
            s2 = s2 << _11 ^ s2 >> _11 ^ b[(a ^ s1 ^ s2 >> _11) & mask] << _23
            s2 = s2 << _4 ^ s2 >> _23 ^ b[(bit ^ a >> _8 ^ a ^ s2 >> _10) & mask] << _1

            s1 = s2 << _3 ^ s2 >> _1 ^ h[i] ^ bit
            a = a << _9 ^ a >> _7 ^ s1 >> _1 ^ b[(s2 >> _1 ^ h[i]) & mask] << _5

            s1, s2, s3 = s3, s1, s2
            hash_bytes[i] = b[a & mask] ^ b[h[i] & mask]

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
        print("pylxr: initializing the table...")
        for i in self.byte_map:
            self.byte_map[i] = u64(i)

        # Now what we want to do is just mix it all up.  Take every byte in the ByteMap list, and exchange it
        # for some other byte in the ByteMap list. Note that we do this over and over, mixing and more mixing
        # the ByteMap, but maintaining the ratio of each byte value in the ByteMap list.
        print("pylxr: shuffling the table...")
        for loop in range(self.passes):
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
            print(f"pylxr: pass {loop} completed (time taken: {time})")

    def _read_table(self):
        home = os.getenv("HOME")
        path = f"{home}/.lxrhash"

        if not os.path.exists(path):
            os.mkdir(path)

        filename = f"{path}/lxrhash-seed-{self.seed.hex()}-passes-{self.passes}-size-{self.map_size_bits}.dat"
        if self.verbose:
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
            if self.verbose:
                print("Table not found, Generating ByteMap Table")
            self._generate_table()
            if self.verbose:
                print("Writing ByteMap Table")
            with open(filename, "wb+") as f:
                f.write(self.byte_map)

        if self.verbose:
            print(f"Done. Total time taken: {datetime.datetime.now() - start}")
