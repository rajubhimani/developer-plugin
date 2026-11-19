#include "{{package}}.h"

int {{package}}_run(int argc, char **argv, FILE *out, FILE *err) {
    if (argc != 2 || argv[1][0] == '\0') {
        fprintf(err, "usage: {{name}} <name>\n");
        return {{package_upper}}_EXIT_USAGE;
    }
    if (fprintf(out, "Hello, %s!\n", argv[1]) < 0) {
        return {{package_upper}}_EXIT_ERROR;
    }
    return {{package_upper}}_EXIT_OK;
}
