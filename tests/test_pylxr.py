import unittest

import timeit
import pylxr


class TestHash(unittest.TestCase):
    def setUp(self) -> None:
        self.lxr = pylxr.LXR(map_size_bits=25)

    def test_hash(self):
        b = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc dapibus pretium urna, mollis aliquet elit cursus ac. Sed sodales, erat ut volutpat viverra, ante urna pretium est, non congue augue dui sed purus. Mauris vitae mollis metus. Fusce convallis faucibus tempor. Maecenas hendrerit, urna eu lobortis venenatis, neque leo consequat enim, nec placerat tellus eros quis diam. Donec quis vestibulum eros. Maecenas id vulputate justo. Quisque nec feugiat nisi, lacinia pulvinar felis. Pellentesque habitant sed."
        h = self.lxr.h(b)
        assert h.hex() == "acf038ca9271d6619499c81458941ddf5eeaba38e8f4c822d42844dd56e21d4f", f"Got: {h.hex()}"

    def test_timing(self):
        t = timeit.timeit('lxr.h(b"HASH")', number=10000, globals={'lxr': self.lxr})
        print(t)


if __name__ == '__main__':
    unittest.main()
