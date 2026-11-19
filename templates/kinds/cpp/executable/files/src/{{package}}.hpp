#pragma once

#include <iosfwd>
#include <string>
#include <vector>

namespace {{package}} {

/// Exit codes scripts can rely on.
enum ExitCode : int { kOk = 0, kError = 1, kUsage = 2 };

/// Runs the program with `args` (without the program name). Results go to `out`; messages
/// for people go to `err`. Takes its streams as parameters so tests need no terminal.
[[nodiscard]] int run(const std::vector<std::string>& args, std::ostream& out, std::ostream& err);

}  // namespace {{package}}
