import unittest

import timeit
import pylxr


class TestHash(unittest.TestCase):
    def setUp(self) -> None:
        self.lxr = pylxr.LXR(map_size_bits=30)

    def test_hash(self):
        known_hashes = {
            b"": "66afa4d58ff4b99ef77f7bc2dc7567a23ccb47edab1486fccc3e9556bc64e9cc",
            b"foo": "7dda54f8d5efcd6928870bdc9ece900b320e897bce4814e9010cc08647c197ae",
            b"bar": "fe2cb7f3cef5702a1cb4712434085afe1efdef1d2563291e4883cd2a3ea1e074",
            b"pegnet": "cd45b08c0619d78e2a810c4e6462296ec51ae4fd0f73a54a154a97a54942297e",
        }
        for src, hash_hex in known_hashes.items():
            h = self.lxr.h(src)
            assert h.hex() == hash_hex

    def test_timing(self):
        t = timeit.timeit('lxr.h(b"HASH")', number=10000, globals={'lxr': self.lxr})
        print(t)


if __name__ == '__main__':
    unittest.main()
