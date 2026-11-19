#include "{{package}}.hpp"

#include <ostream>

namespace {{package}} {

int run(const std::vector<std::string>& args, std::ostream& out, std::ostream& err) {
    if (args.size() != 1 || args.front().empty()) {
        err << "usage: {{name}} <name>\n";
        return kUsage;
    }
    out << "Hello, " << args.front() << "!\n";
    return out ? kOk : kError;
}

}  // namespace {{package}}
