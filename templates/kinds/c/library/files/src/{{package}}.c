#include "{{package}}/{{package}}.h"

#include <stdio.h>

{{package}}_status {{package}}_greet(const char *name, char *out, size_t out_size) {
    if (out == NULL || out_size == 0) {
        return {{package_upper}}_ERR_INVALID_ARGUMENT;
    }
    out[0] = '\0';
    if (name == NULL || name[0] == '\0') {
        return {{package_upper}}_ERR_INVALID_ARGUMENT;
    }
    int written = snprintf(out, out_size, "Hello, %s!", name);
    if (written < 0) {
        out[0] = '\0';
        return {{package_upper}}_ERR_INVALID_ARGUMENT;
    }
    if ((size_t)written >= out_size) {
        out[0] = '\0';
        return {{package_upper}}_ERR_BUFFER_TOO_SMALL;
    }
    return {{package_upper}}_OK;
}
