__all__ = [
    '__version__',
]

# version set by poetry build though poetry-dynamic-version-plugin
__version__ = '0.0.0'

# for local development, we use the file _version.py which is ignored by git
try:
    from ._version import __version__
except ImportError:
    pass

__version__ = '0.4.0'  # noqa
