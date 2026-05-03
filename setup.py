"""Legacy setuptools entrypoint.

Primary project metadata lives in ``pyproject.toml``.
This file is kept as a thin compatibility shim for tooling that still
expects ``setup.py`` to exist.
"""

from setuptools import setup

setup()
