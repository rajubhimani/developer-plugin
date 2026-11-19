#pragma once

#include <string>
#include <string_view>

namespace {{package}} {

/// Returns "Hello, <name>!". Throws std::invalid_argument when `name` is empty.
/// Replace with the library's real behaviour; every public function documents what it
/// throws and who owns what it returns.
[[nodiscard]] std::string greet(std::string_view name);

}  // namespace {{package}}
