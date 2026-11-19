/* Entry point: keep it thin. The logic is {{package}}_run, which tests call directly. */
#include <stdio.h>

#include "{{package}}.h"

int main(int argc, char **argv) {
    return {{package}}_run(argc, argv, stdout, stderr);
}
