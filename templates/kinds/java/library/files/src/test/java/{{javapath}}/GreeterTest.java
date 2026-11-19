package {{javapkg}};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class GreeterTest {

  @Test
  void greets() {
    assertEquals("Hello, world!", Greeter.greet("world"));
  }

  @Test
  void rejectsABlankName() {
    assertThrows(IllegalArgumentException.class, () -> Greeter.greet("  "));
  }

  @Test
  void rejectsNull() {
    assertThrows(NullPointerException.class, () -> Greeter.greet(null));
  }
}
