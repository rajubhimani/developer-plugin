#include <iostream>
#include <stdexcept>

#include "{{package}}/{{package}}.hpp"

// A check that still runs in release builds (assert does not). Replace with a maintained
// test framework (Catch2 or GoogleTest) when the suite grows.
static int failures = 0;
#define CHECK(cond)                                                                   \
    do {                                                                              \
        if (!(cond)) {                                                                \
            std::cerr << __FILE__ << ':' << __LINE__ << ": check failed: " #cond "\n"; \
            ++failures;                                                               \
        }                                                                             \
    } while (false)

int main() {
    CHECK({{package}}::greet("world") == "Hello, world!");

    bool threw = false;
    try {
        static_cast<void>({{package}}::greet(""));
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    CHECK(threw);

    return failures == 0 ? 0 : 1;
}
