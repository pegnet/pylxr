from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize, build_ext


deps = {"pylxr": ["numpy", "cython"]}

extensions = [Extension(name="cpylxr", sources=["cpylxr.pyx"])]

setup(
    name="pylxr",
    version="0.0.3",
    description="A small library for using PegNet's custom LXR Hash",
    author="Sam Barnes",
    author_email="sambarnes@factom.com",
    url="https://github.com/pegnet/pylxr",
    keywords=["lxr", "hash", "pegnet", "factom"],
    license="MIT",
    py_modules=["pylxr"],
    ext_modules=cythonize(extensions),
    install_requires=deps["pylxr"],
    zip_safe=False,
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    build_ext=build_ext,
)
