"""{{title}}: <one line: what this library does>.

The public API is exactly what `__all__` lists. Anything else, and every module whose
name starts with an underscore, is private and may change in any release. Changing
the public API follows semantic versioning (see docs/api.md).
"""

from importlib.metadata import PackageNotFoundError, version

from {{package}}._greeting import greet

try:
    __version__ = version("{{name}}")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0+unknown"

__all__ = ["__version__", "greet"]
