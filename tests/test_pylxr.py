import unittest

import timeit
import pylxr


class TestHash(unittest.TestCase):
    def setUp(self) -> None:
        self.lxr = pylxr.LXR(map_size_bits=30)

    def test_hash(self):
        known_hashes = {
            b"": "66afa4d58ff4b99ef77f7bc2dc7567a23ccb47edab1486fccc3e9556bc64e9cc",
            b"abcde": "00e9ef8262f154b6aef3b4bb1a95644bbd651040df34c3d88dd696d519445989",
            b"bar": "66a7c02adcf00ed55a11877fa543ccc27a0a4c59268cc36cd8fe9616ce6cda63",
            b"foo": "93a2eaf76b8cc21610601fb5a87f8f6ea57ef0fc1e6eaf414e7b6eac186bca16",
            b"pegnet": "84c5bc3b47965e0fff9e66871b94dd7d2cd1f866102a6c1cd7ef30eb3ee737ef",
            b"0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "e169f393b60ef4e74fa2b3f514451523911a3c9929c76b39bd46f448979e784f",
            b"1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "da715b359c07e94c3db8e7ca0fb2786ffc1d40cae2d02d4d193da4c5f0b28e6c",
            b"2000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "fe788f9bb86a3b014f1b7b5247bee1f88471a795f17d3d8d9555a2d74dd56a66",
            b"3000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "3122704067ec22284d47f8ed30e2e218bab4b9885c951f5578ae958ea88d2242",
            b"4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "81d4ba04b98fa2d9af34af88323904be70c0dc47bd4cbf5d5ba39ff684a41cf0",
            b"5000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000": "aece6cc62f94ea08c7289d52caeee7d239efecfc72fac11b78bee157675939f5",
            b"0000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000": "f84af0f18a9be4d89194b658027ba2e4d55ec0d6ad681ba6667e43f27c1cbf63",
            b"0000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000": "0b526f63210add8d7984bbd0ef1cffd2e3fc263a1fd548bdb8a4e33b7838e8c4",
            b"0000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000": "434395f5efa71773c2b4b2f4c0fd9d5a88b2010002080fa54cb4a8163bcb827c",
            b"0000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000": "42372a30bbc752c654e072b06d680ad77357caf87353a0f4e3e012158fa6928f",
            b"0000000000000000000000000000000000000000000000005000000000000000000000000000000000000000000000000000000": "136187976bca29b0d77ca8f29846e81e3f6111dcf016f5f0e78bd912db6180e1",
            b"0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001": "2079f06de6d91efa953667e16fdfb573f2d0196c0d5ffd7f3a27243497a26a33",
            b"0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002": "b4ed552867c41fcc73190374b38188a424f014d906d2d8603bc68995fcee82da",
            b"0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003": "89d32d663342ef54d27ce87ee1da784c239921954393a083c63564fd4be98f57",
            b"0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004": "211dc5cbe8003e7c992f4d82788c9bb76cd69d7623cb78b1454266b57248852e",
        }
        for src, hash_hex in known_hashes.items():
            h = self.lxr.h(src)
            assert h.hex() == hash_hex, f"observed ({h.hex()}) != expected({hash_hex})"

    def test_timing(self):
        t = timeit.timeit('lxr.h(b"HASH")', number=10000, globals={"lxr": self.lxr})
        print(t)


if __name__ == "__main__":
    unittest.main()
