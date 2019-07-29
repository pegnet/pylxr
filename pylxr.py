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
    byte_map: np.nbytes = field(init=False)

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

        b = lambda x: u64(self.byte_map[x & mask])

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

        index = u64(0)
        for bit in src:
            bit = u64(bit)
            if index >= self.hash_size:
                index = u64(0)
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
            s1 = s1 << u64(9) ^ s1 >> u64(1) ^ a ^ b(a >> u64(5) ^ bit) << u64(3)
            s1 = s1 << u64(5) ^ s1 >> u64(3) ^ b(s1 ^ bit) << u64(7)
            s1 = s1 << u64(7) ^ s1 >> u64(7) ^ b(a ^ s1 >> u64(7)) << u64(5)
            s1 = s1 << u64(11) ^ s1 >> u64(5) ^ b(bit ^ a >> u64(11) ^ s1) << u64(27)

            h[index] = s1 ^ a ^ h[index] << u64(7) ^ h[index] >> u64(13)

            a = a << u64(17) ^ a >> u64(5) ^ s1 ^ b(a ^ s1 >> u64(27) ^ bit) << u64(3)
            a = a << u64(13) ^ a >> u64(3) ^ b(a ^ s1) << u64(7)
            a = a << u64(15) ^ a >> u64(7) ^ b(a >> u64(7) ^ s1) << u64(11)
            a = a << u64(9) ^ a >> u64(11) ^ b(bit ^ a ^ s1) << u64(3)

            s1 = s1 << u64(7) ^ s1 >> u64(27) ^ a ^ b(a >> u64(3)) << u64(13)
            s1 = s1 << u64(3) ^ s1 >> u64(13) ^ b(s1 ^ bit) << u64(11)
            s1 = s1 << u64(8) ^ s1 >> u64(11) ^ b(a ^ s1 >> u64(11)) << u64(9)
            s1 = s1 << u64(6) ^ s1 >> u64(9) ^ b(bit ^ a ^ s1) << u64(3)

            a = a << u64(23) ^ a >> u64(3) ^ s1 ^ b(a ^ bit ^ s1 >> u64(3)) << u64(7)
            a = a << u64(17) ^ a >> u64(7) ^ b(a ^ s1 >> u64(3)) << u64(5)
            a = a << u64(13) ^ a >> u64(5) ^ b(a >> u64(5) ^ s1) << u64(1)
            a = a << u64(11) ^ a >> u64(1) ^ b(bit ^ a ^ s1) << u64(7)

            s1 = s1 << u64(5) ^ s1 >> u64(3) ^ a ^ b(a >> u64(7) ^ s1 >> u64(3)) << u64(6)
            s1 = s1 << u64(8) ^ s1 >> u64(6) ^ b(s1 ^ bit) << u64(11)
            s1 = s1 << u64(11) ^ s1 >> u64(11) ^ b(a ^ s1 >> u64(11)) << u64(5)
            s1 = s1 << u64(7) ^ s1 >> u64(5) ^ b(bit ^ a >> u64(7) ^ a ^ s1) << u64(17)

            s2 = s2 << u64(3) ^ s2 >> u64(17) ^ s1 ^ b(a ^ s2 >> u64(5) ^ bit) << u64(13)
            s2 = s2 << u64(6) ^ s2 >> u64(13) ^ b(s2) << u64(11)
            s2 = s2 << u64(11) ^ s2 >> u64(11) ^ b(a ^ s1 ^ s2 >> u64(11)) << u64(23)
            s2 = s2 << u64(4) ^ s2 >> u64(23) ^ b(bit ^ a >> u64(8) ^ a ^ s2 >> u64(10)) << u64(1)

            s1 = s2 << u64(3) ^ s2 >> u64(1) ^ h[index] ^ bit
            a = a << u64(9) ^ a >> u64(7) ^ s1 >> u64(1) ^ b(s2 >> u64(1) ^ h[index]) << u64(5)

            s1, s2, s3 = s3, s1, s2
            index += u64(1)

        # Reduction pass
        # Done by iterating over hs[] to produce the bytes[] hash
        #
        # At this point, we have HBits of state in hs.  We need to reduce them down to a byte,
        # And we do so by doing a bit more bitwise math, and mapping the values through our byte map.

        hash_bytes = bytearray(self.hash_size)
        # Roll over all the hs (one int64 value for every byte in the resulting hash) and reduce them to byte values
        for i, bit in enumerate(h):
            # Duplicated from above to reduce function call overhead
            s1 = s1 << u64(9) ^ s1 >> u64(1) ^ a ^ b(a >> u64(5) ^ bit) << u64(3)
            s1 = s1 << u64(5) ^ s1 >> u64(3) ^ b(s1 ^ bit) << u64(7)
            s1 = s1 << u64(7) ^ s1 >> u64(7) ^ b(a ^ s1 >> u64(7)) << u64(5)
            s1 = s1 << u64(11) ^ s1 >> u64(5) ^ b(bit ^ a >> u64(11) ^ s1) << u64(27)

            h[i] = s1 ^ a ^ h[i] << u64(7) ^ h[i] >> u64(13)

            a = a << u64(17) ^ a >> u64(5) ^ s1 ^ b(a ^ s1 >> u64(27) ^ bit) << u64(3)
            a = a << u64(13) ^ a >> u64(3) ^ b(a ^ s1) << u64(7)
            a = a << u64(15) ^ a >> u64(7) ^ b(a >> u64(7) ^ s1) << u64(11)
            a = a << u64(9) ^ a >> u64(11) ^ b(bit ^ a ^ s1) << u64(3)

            s1 = s1 << u64(7) ^ s1 >> u64(27) ^ a ^ b(a >> u64(3)) << u64(13)
            s1 = s1 << u64(3) ^ s1 >> u64(13) ^ b(s1 ^ bit) << u64(11)
            s1 = s1 << u64(8) ^ s1 >> u64(11) ^ b(a ^ s1 >> u64(11)) << u64(9)
            s1 = s1 << u64(6) ^ s1 >> u64(9) ^ b(bit ^ a ^ s1) << u64(3)

            a = a << u64(23) ^ a >> u64(3) ^ s1 ^ b(a ^ bit ^ s1 >> u64(3)) << u64(7)
            a = a << u64(17) ^ a >> u64(7) ^ b(a ^ s1 >> u64(3)) << u64(5)
            a = a << u64(13) ^ a >> u64(5) ^ b(a >> u64(5) ^ s1) << u64(1)
            a = a << u64(11) ^ a >> u64(1) ^ b(bit ^ a ^ s1) << u64(7)

            s1 = s1 << u64(5) ^ s1 >> u64(3) ^ a ^ b(a >> u64(7) ^ s1 >> u64(3)) << u64(6)
            s1 = s1 << u64(8) ^ s1 >> u64(6) ^ b(s1 ^ bit) << u64(11)
            s1 = s1 << u64(11) ^ s1 >> u64(11) ^ b(a ^ s1 >> u64(11)) << u64(5)
            s1 = s1 << u64(7) ^ s1 >> u64(5) ^ b(bit ^ a >> u64(7) ^ a ^ s1) << u64(17)

            s2 = s2 << u64(3) ^ s2 >> u64(17) ^ s1 ^ b(a ^ s2 >> u64(5) ^ bit) << u64(13)
            s2 = s2 << u64(6) ^ s2 >> u64(13) ^ b(s2) << u64(11)
            s2 = s2 << u64(11) ^ s2 >> u64(11) ^ b(a ^ s1 ^ s2 >> u64(11)) << u64(23)
            s2 = s2 << u64(4) ^ s2 >> u64(23) ^ b(bit ^ a >> u64(8) ^ a ^ s2 >> u64(10)) << u64(1)

            s1 = s2 << u64(3) ^ s2 >> u64(1) ^ h[i] ^ bit
            a = a << u64(9) ^ a >> u64(7) ^ s1 >> u64(1) ^ b(s2 >> u64(1) ^ h[i]) << u64(5)

            s1, s2, s3 = s3, s1, s2
            hash_bytes[i] = b(a) ^ b(h[i])

        return bytes(hash_bytes)

    def _generate_table(self):
        # Our own "random" generator that really is just used to shuffle values
        first_rand = 2458719153079158768
        first_b = 4631534797403582785
        first_v = 3523455478921636871

        offset = self.seed_int ^ first_rand
        b = self.seed_int ^ first_b
        v = first_v
        mask = self.map_size - 1

        # Fill the ByteMap with bytes ranging from 0 to 255.  As long as map_size % 256 == 0, this
        # looping and masking works just fine.
        print("Initializing the Table")
        for i in self.byte_map:
            self.byte_map[i] = i

        # Now what we want to do is just mix it all up.  Take every byte in the ByteMap list, and exchange it
        # for some other byte in the ByteMap list. Note that we do this over and over, mixing and more mixing
        # the ByteMap, but maintaining the ratio of each byte value in the ByteMap list.
        print("Shuffling the Table")
        for loop in range(self.passes):
            print(f"Pass {loop}")
            for iteration, i in enumerate(self.byte_map):
                # The random index used to shuffle the ByteMap is itself computed through the ByteMap table
                # in a deterministic pattern.
                offset = offset << 9 ^ offset >> 1 ^ offset >> 7 ^ b
                v = self.byte_map[(offset ^ b) & mask] ^ v << 8 ^ v >> 1
                b = v << 7 ^ v << 13 ^ v << 33 ^ v << 52 ^ b << 9 ^ b >> 1
                j = offset & mask
                self.byte_map[i], self.byte_map[j] = self.byte_map[j], self.byte_map[i]
            n = len(self.byte_map) / 1024000
            print(f" Index {n} Meg of {n} Meg -- Pass is 100% Complete")

    def _read_table(self):
        home = os.getenv("HOME")
        path = f"{home}/.lxrhash"

        if not os.path.exists(path):
            os.mkdir(path)

        filename = f"{path}/lxrhash-seed-{self.seed.hex()}-passes-{self.passes}-size-{self.map_size_bits}.dat"
        print(f"Reading ByteMap Table {filename}")
        start = datetime.datetime.now()
        found = False
        with open(filename, "rb+") as f:
            data = f.read()
            if len(data) == self.map_size:
                self.byte_map = bytearray()
                self.byte_map.extend(data)
                found = True

        if not found:
            print("Table not found, Generating ByteMap Table")
            self._generate_table()
            print("Writing ByteMap Table")
            with open(filename, "wb+") as f:
                f.write(self.byte_map)

        print(f"Done. Total time taken: {datetime.datetime.now() - start}")
