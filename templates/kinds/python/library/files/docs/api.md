# Public API

The public API is what `{{package}}.__all__` lists and nothing else. Private modules
start with an underscore and may change in any release.

| Name | Kind | Since | Notes |
|---|---|---|---|
| `greet(name)` | function | 0.1.0 | Returns a greeting; raises `ValueError` for an empty name |
| `__version__` | string | 0.1.0 | The installed version |

## Rules for changing it

- **Add** a name: a minor version. Add it to `__all__`, this table and the tests.
- **Change behaviour** or a signature in a way existing callers notice: a major
  version, after a deprecation period of at least one minor release.
- **Deprecate** with a warning that names the replacement and the version that
  removes it, and list it in the changelog.
- **Remove** a name only in a major version.
- Support for Python releases follows the `requires-python` line in `pyproject.toml`;
  dropping one is a minor version at least, and is noted in the changelog.
