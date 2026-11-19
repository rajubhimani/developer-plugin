package {{javapkg}}.domain;

/** An item broke a business rule. */
public class InvalidItemException extends RuntimeException {

  private static final long serialVersionUID = 1L;

  /**
   * Creates the exception.
   *
   * @param message what rule was broken
   */
  public InvalidItemException(String message) {
    super(message);
  }
}
