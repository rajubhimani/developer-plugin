package {{javapkg}};

/** Entry point: keep it thin. The logic is {@link Cli#run}, which tests call directly. */
public final class Main {

  private Main() {}

  /**
   * Runs the command and exits with its code.
   *
   * @param args the command line arguments
   */
  public static void main(String[] args) {
    System.exit(new Cli(System.out, System.err).run(args));
  }
}
