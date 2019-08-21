import cpylxr
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
        src_arr = np.frombuffer(src, dtype=np.uint8).astype(np.uint8)
        return cpylxr.h(self.map_size_bits, self.byte_map, src_arr).astype(np.uint8).tobytes()

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
            self.byte_map = np.memmap(filename, dtype=np.uint8)
            if len(self.byte_map) == self.map_size:
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
