import unittest

import timeit
import pylxr


class TestHash(unittest.TestCase):
    def setUp(self) -> None:
        self.lxr = pylxr.LXR(map_size_bits=25)

    def test_hash(self):
        h = self.lxr.h(b"HASH")
        assert h.hex() == "7b77a3c9cef19f4c68df98c668027c8cb7035fbb565927fbcafea4dfa4f1fa8a", f"Got: {h.hex()}"

    def test_timing(self):
        t = timeit.timeit('lxr.h(b"HASH")', number=10000, globals={'lxr': self.lxr})
        print(t)


if __name__ == '__main__':
    unittest.main()
