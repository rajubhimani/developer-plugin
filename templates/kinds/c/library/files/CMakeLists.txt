cmake_minimum_required(VERSION 3.25)
project({{name}} VERSION 0.1.0 LANGUAGES C)

# Set to the C standard you support (look up the current one; see the lang-c skill).
set(CMAKE_C_STANDARD <c-standard>)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# One interface target carries the warning and sanitizer flags, so the library, the tests
# and the program are built the same way. Warnings are errors, deprecated calls included.
add_library({{package}}_options INTERFACE)
target_compile_options({{package}}_options INTERFACE
  $<$<C_COMPILER_ID:MSVC>:/W4 /WX>
  $<$<NOT:$<C_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wdeprecated-declarations -Werror>)
option({{package_upper}}_SANITIZE "Build with address and undefined-behaviour sanitizers" OFF)
if({{package_upper}}_SANITIZE AND NOT MSVC)
  target_compile_options({{package}}_options INTERFACE -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options({{package}}_options INTERFACE -fsanitize=address,undefined)
endif()

add_library({{package}} src/{{package}}.c)
add_library({{name}}::{{package}} ALIAS {{package}})
target_include_directories({{package}} PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>" "$<INSTALL_INTERFACE:include>")
target_link_libraries({{package}} PRIVATE {{package}}_options)

enable_testing()
add_executable(test_{{package}} tests/test_{{package}}.c)
target_link_libraries(test_{{package}} PRIVATE {{package}} {{package}}_options)
add_test(NAME {{package}} COMMAND test_{{package}})

install(TARGETS {{package}} ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include)
