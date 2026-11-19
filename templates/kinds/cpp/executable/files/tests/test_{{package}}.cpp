#include <iostream>
#include <sstream>

#include "{{package}}.hpp"

static int failures = 0;
#define CHECK(cond)                                                                   \
    do {                                                                              \
        if (!(cond)) {                                                                \
            std::cerr << __FILE__ << ':' << __LINE__ << ": check failed: " #cond "\n"; \
            ++failures;                                                               \
        }                                                                             \
    } while (false)

int main() {
    std::ostringstream out;
    std::ostringstream err;
    CHECK({{package}}::run({"world"}, out, err) == {{package}}::kOk);
    CHECK(out.str() == "Hello, world!\n");

    std::ostringstream out2;
    std::ostringstream err2;
    CHECK({{package}}::run({}, out2, err2) == {{package}}::kUsage);
    CHECK(out2.str().empty());
    CHECK(!err2.str().empty());

    return failures == 0 ? 0 : 1;
}
