#include "{{package}}/{{package}}.hpp"

#include <stdexcept>
#include <string>

namespace {{package}} {

std::string greet(std::string_view name) {
    if (name.empty()) {
        throw std::invalid_argument("name must not be empty");
    }
    std::string greeting = "Hello, ";
    greeting += name;
    greeting += '!';
    return greeting;
}

}  // namespace {{package}}
