# {{title}}

<one line: what this library does>

```bash
make install     # configure the debug preset
make check       # format check, clang-tidy, tests with sanitizers
make build       # release build
```

```cpp
#include <{{package}}/{{package}}.hpp>

auto text = {{package}}::greet("world");
```

Set `CMAKE_CXX_STANDARD` in `CMakeLists.txt` to the C++ standard you support. The public
interface is the headers under `include/{{package}}/`; see [docs/api.md](docs/api.md). Own
resources with RAII, avoid owning raw pointers, document what each function throws. Warnings
are errors, deprecated calls included, and the `asan` preset runs the tests under the
address and undefined-behaviour sanitizers.
