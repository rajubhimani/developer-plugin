// Entry point: keep it thin. The logic is {{package}}::run, which tests call directly.
#include <iostream>
#include <string>
#include <vector>

#include "{{package}}.hpp"

int main(int argc, char** argv) {
    const std::vector<std::string> args(argv + 1, argv + argc);
    return {{package}}::run(args, std::cout, std::cerr);
}
