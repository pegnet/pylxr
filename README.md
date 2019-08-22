# pyLXR

Another implementation of the [LXRHash](https://github.com/pegnet/LXRHash) hashing algorithm used for PegNet's PoW.

A python library that wraps WhoSoup's [C implementation](https://github.com/WhoSoup/lxrhash-benchmark-c/blob/master/main.c) for performance.

Note: map generation is not tested or optimized yet. It is **highly** recommended to just use a prebuilt map from the go implementation linked above.

## Installation

Not on pypi just yet, so just build from source:
```
git clone git@github.com:pegnet/pylxr
cd pylxr && python3 setup.py install
```
