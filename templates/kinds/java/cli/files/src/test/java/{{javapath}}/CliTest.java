package {{javapkg}};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class CliTest {

  private final ByteArrayOutputStream out = new ByteArrayOutputStream();
  private final ByteArrayOutputStream err = new ByteArrayOutputStream();
  private final Cli cli =
      new Cli(
          new PrintStream(out, true, StandardCharsets.UTF_8),
          new PrintStream(err, true, StandardCharsets.UTF_8));

  @Test
  void greets() {
    assertEquals(Cli.EXIT_OK, cli.run("world"));
    assertEquals("Hello, world!" + System.lineSeparator(), out.toString(StandardCharsets.UTF_8));
  }

  @Test
  void noArgumentIsAUsageError() {
    assertEquals(Cli.EXIT_USAGE, cli.run());
    assertEquals("", out.toString(StandardCharsets.UTF_8));
    assertTrue(err.toString(StandardCharsets.UTF_8).contains("usage"));
  }
}
