package {{javapkg}};

import java.util.Objects;

/**
 * The public API of this library. Everything public in this package is a promise to callers and
 * follows semantic versioning; keep implementation details package-private.
 */
public final class Greeter {

  private Greeter() {}

  /**
   * Returns a greeting for {@code name}. Replace with the library's real behaviour.
   *
   * @param name who to greet; must not be {@code null} or blank
   * @return the greeting
   * @throws NullPointerException if {@code name} is {@code null}
   * @throws IllegalArgumentException if {@code name} is blank
   */
  public static String greet(String name) {
    Objects.requireNonNull(name, "name");
    if (name.isBlank()) {
      throw new IllegalArgumentException("name must not be empty");
    }
    return "Hello, " + name + "!";
  }
}
