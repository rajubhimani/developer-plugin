#ifndef {{package_upper}}_H
#define {{package_upper}}_H

#include <stdio.h>

/* Exit codes scripts can rely on. */
enum { {{package_upper}}_EXIT_OK = 0, {{package_upper}}_EXIT_ERROR = 1, {{package_upper}}_EXIT_USAGE = 2 };

/* Runs the program with the given arguments. Results go to out; messages for people go to
 * err. Returns the exit code. Takes its streams as parameters so tests need no terminal. */
int {{package}}_run(int argc, char **argv, FILE *out, FILE *err);

#endif /* {{package_upper}}_H */
