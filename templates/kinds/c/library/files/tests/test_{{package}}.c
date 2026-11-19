#include <stdio.h>
#include <string.h>

#include "{{package}}/{{package}}.h"

/* A check that still runs in release builds (assert does not). */
static int failures = 0;
#define CHECK(cond)                                                                \
    do {                                                                           \
        if (!(cond)) {                                                             \
            fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #cond); \
            failures++;                                                            \
        }                                                                          \
    } while (0)

int main(void) {
    char buf[32];
    CHECK({{package}}_greet("world", buf, sizeof buf) == {{package_upper}}_OK);
    CHECK(strcmp(buf, "Hello, world!") == 0);

    CHECK({{package}}_greet("", buf, sizeof buf) == {{package_upper}}_ERR_INVALID_ARGUMENT);
    CHECK({{package}}_greet(NULL, buf, sizeof buf) == {{package_upper}}_ERR_INVALID_ARGUMENT);
    CHECK({{package}}_greet("world", NULL, sizeof buf) == {{package_upper}}_ERR_INVALID_ARGUMENT);

    char small[4];
    CHECK({{package}}_greet("world", small, sizeof small) == {{package_upper}}_ERR_BUFFER_TOO_SMALL);
    CHECK(small[0] == '\0'); /* never a half-written string */

    return failures == 0 ? 0 : 1;
}
