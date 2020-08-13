from setuptools import setup
from Cython.Build import cythonize

# distutils: language = c++

cy = cythonize(
    "hello.pyx",
    compiler_directives={
        "language_level": 3
    }
)

setup(
    name='Hello world app',
    ext_modules=cy,
    zip_safe=False,
)
