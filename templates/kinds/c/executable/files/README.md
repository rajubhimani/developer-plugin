# {{title}}

<one line: what this program does>

```bash
make install && make build && ./build/release/{{name}} world
make check
```

`src/main.c` only passes the arguments and streams to `{{package}}_run`; the logic and its
tests live there. Exit code 0 is success, 2 is bad usage, 1 is any other failure. Results
go to standard output, messages for people to standard error. Set `CMAKE_C_STANDARD` in
`CMakeLists.txt`. Warnings are errors, deprecated calls included, and the `asan` preset runs
the tests under the address and undefined-behaviour sanitizers.
