#include <stdio.h>
#include <string.h>

#include "{{package}}.h"

static int failures = 0;
#define CHECK(cond)                                                                \
    do {                                                                           \
        if (!(cond)) {                                                             \
            fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #cond); \
            failures++;                                                            \
        }                                                                          \
    } while (0)

/* Run the program with a temporary file standing in for each stream. */
static int run_with(int argc, char **argv, char *out_text, size_t out_size) {
    FILE *out = tmpfile();
    FILE *err = tmpfile();
    int code = {{package}}_run(argc, argv, out, err);
    rewind(out);
    size_t n = fread(out_text, 1, out_size - 1, out);
    out_text[n] = '\0';
    fclose(out);
    fclose(err);
    return code;
}

int main(void) {
    char text[64];
    char *good[] = {"{{name}}", "world"};
    CHECK(run_with(2, good, text, sizeof text) == {{package_upper}}_EXIT_OK);
    CHECK(strcmp(text, "Hello, world!\n") == 0);

    char *none[] = {"{{name}}"};
    CHECK(run_with(1, none, text, sizeof text) == {{package_upper}}_EXIT_USAGE);
    CHECK(text[0] == '\0');

    return failures == 0 ? 0 : 1;
}
