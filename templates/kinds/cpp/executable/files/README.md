# {{title}}

<one line: what this program does>

```bash
make install && make build && ./build/release/{{name}} world
make check
```

`src/main.cpp` only turns `argv` into a vector and calls `{{package}}::run`; the logic and its
tests live there. Exit code 0 is success, 2 is bad usage, 1 is any other failure. Results go
to standard output, messages for people to standard error. Set `CMAKE_CXX_STANDARD` in
`CMakeLists.txt`. Warnings are errors, deprecated calls included, and the `asan` preset runs
the tests under the address and undefined-behaviour sanitizers.
