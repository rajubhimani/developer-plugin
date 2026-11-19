# {{title}}

<one line: what this library does>

```bash
make install     # configure the debug preset
make check       # format check, clang-tidy, tests with sanitizers
make build       # release build
```

```c
#include <{{package}}/{{package}}.h>

char out[64];
if ({{package}}_greet("world", out, sizeof out) == {{package_upper}}_OK) puts(out);
```

Set `CMAKE_C_STANDARD` in `CMakeLists.txt` to the C standard you support. The public
interface is the header under `include/{{package}}/`; see [docs/api.md](docs/api.md).
Every public function documents who owns each buffer and what it returns on failure.
Warnings are errors, deprecated calls included, and the `asan` preset runs the tests under
the address and undefined-behaviour sanitizers. Add a fuzz target for every function that
parses untrusted bytes.
