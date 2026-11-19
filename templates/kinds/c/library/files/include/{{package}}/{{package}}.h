#ifndef {{package_upper}}_H
#define {{package_upper}}_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Result of every function that can fail: zero is success. */
typedef enum {
    {{package_upper}}_OK = 0,
    {{package_upper}}_ERR_INVALID_ARGUMENT = 1,
    {{package_upper}}_ERR_BUFFER_TOO_SMALL = 2
} {{package}}_status;

/* Writes "Hello, <name>!" and a terminating NUL into out, which holds out_size bytes.
 * Ownership: the caller owns both buffers; the library keeps no pointer.
 * Never writes past out_size. On failure out is left as an empty string when out_size > 0.
 * Returns {{package_upper}}_ERR_INVALID_ARGUMENT for a NULL or empty name or a NULL out. */
{{package}}_status {{package}}_greet(const char *name, char *out, size_t out_size);

#ifdef __cplusplus
}
#endif

#endif /* {{package_upper}}_H */
