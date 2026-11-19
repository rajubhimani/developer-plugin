package {{javapkg}};

import java.io.PrintStream;

/**
 * The command's logic. It takes its streams as parameters, so tests need no terminal. Results go to
 * the output stream; messages for people go to the error stream.
 */
public final class Cli {

  /** Success. */
  public static final int EXIT_OK = 0;

  /** Any other failure. */
  public static final int EXIT_ERROR = 1;

  /** Bad usage. */
  public static final int EXIT_USAGE = 2;

  private final PrintStream out;
  private final PrintStream err;

  /**
   * Creates the command.
   *
   * @param out where results go
   * @param err where messages for people go
   */
  public Cli(PrintStream out, PrintStream err) {
    this.out = out;
    this.err = err;
  }

  /**
   * Runs the command.
   *
   * @param args the arguments, without the program name
   * @return the exit code
   */
  public int run(String... args) {
    if (args.length != 1 || args[0].isBlank()) {
      err.println("usage: {{name}} <name>");
      return EXIT_USAGE;
    }
    out.println("Hello, " + args[0] + "!");
    return EXIT_OK;
  }
}
