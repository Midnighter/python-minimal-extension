#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import (absolute_import, print_function)

import io
import os
import re
from glob import glob
from os.path import (basename, dirname, join, relpath, splitext)

from setuptools import (Extension, find_packages, setup)
from setuptools.command.build_ext import build_ext

try:
    # Allow installing package without any Cython available. This
    # assumes you are going to include the .c files in your sdist.
    import Cython
except ImportError:
    Cython = None


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ).read()


# Enable code coverage for C code: we can"t use CFLAGS=-coverage in tox.ini,
# since that may mess with compiling
# dependencies (e.g. numpy). Therefore we set SETUPPY_CFLAGS=-coverage in
# tox.ini and copy it to CFLAGS here (after deps have been safely installed).
if "TOXENV" in os.environ and "SETUPPY_CFLAGS" in os.environ:
    os.environ["CFLAGS"] = os.environ["SETUPPY_CFLAGS"]


class optional_build_ext(build_ext):
    """Allow the building of C extensions to fail."""
    def run(self):
        try:
            build_ext.run(self)
        except Exception as e:
            self._unavailable(e)
            self.extensions = []  # avoid copying missing files (it would fail).

    def _unavailable(self, e):
        print("*" * 80)
        print("""WARNING:

    An optional code optimization (C extension) could not be compiled.

    Optimizations for this package will not be available!
        """)

        print("CAUSE:")
        print("")
        print("    " + repr(e))
        print("*" * 80)

class DelayedExtension(Extension, object):
    def __init__(self, *args, **kwargs):
        super(DelayedExtension, self).__init__(*args, **kwargs)
        self._include_dirs_hooks = []
        self._include_dirs = None
        self.include_dirs_hook = self._include_dirs_hooks.append

    @property
    def include_dirs(self):
        if "include_dirs" not in self.__dict__:
            include_dirs = self.__dict__["include_dirs"] = list(self._include_dirs or [])
            for hook in self._include_dirs_hooks:
                include_dirs.extend(hook())
        return self.__dict__["include_dirs"]

    @include_dirs.setter
    def include_dirs(self, value):
        self._include_dirs = value

# all these extensions depend on numpy, so no need to distinguish
pkg_extensions = [
    DelayedExtension(
        name=splitext(relpath(path, "src").replace(os.sep, "."))[0],
        sources=[path],
        include_dirs=[dirname(path)]
    )
    for (root, _, _) in os.walk("src")
    for path in glob(join(root, "*.pyx" if Cython else "*.c"))
]

def numpy_hook():
    import numpy
    yield numpy.get_include()

for ext in pkg_extensions:
    ext.include_dirs_hook(numpy_hook)

setup(
    name="",
    version="0.1.0",
    license="BSD 3-Clause License",
    description="Test compiled C extensions with dependencies.",
    long_description="%s\n%s" % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub("", read("README.rst")),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst"))
    ),
    author="Moritz E. Beber",
    author_email="midnighter@posteo.net",
    url="https://github.com/Midnighter/python-minimal-extension",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Cython",
        "Programming Language :: C",
    ],
    keywords=[
        "compile",
        "extension",
        "build",
        "numpy"
    ],
    install_requires=[
        "numpy"
    ],
    setup_requires=[
        "cython",
        "numpy"
    ] if Cython is not None else [
        "numpy"
    ],
    cmdclass={"build_ext": optional_build_ext},
    ext_modules=pkg_extensions,
    tests_require=[
        "tox"
    ],
)
