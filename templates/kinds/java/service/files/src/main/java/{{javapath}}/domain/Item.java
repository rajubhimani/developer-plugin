package {{javapkg}}.domain;

/**
 * A stored item. Business rules live in the domain package, which imports no framework.
 *
 * @param id the identifier assigned by storage
 * @param name the item's name
 */
public record Item(long id, String name) {

  /** The longest name an item may have. */
  public static final int MAX_NAME_LENGTH = 100;

  /**
   * Returns the name trimmed, or throws if it breaks the rules.
   *
   * @param name the raw name, possibly {@code null}
   * @return the cleaned name
   * @throws InvalidItemException if the name is missing, blank or too long
   */
  public static String cleanName(String name) {
    String cleaned = name == null ? "" : name.strip();
    if (cleaned.isEmpty()) {
      throw new InvalidItemException("name must not be empty");
    }
    if (cleaned.length() > MAX_NAME_LENGTH) {
      throw new InvalidItemException("name must be at most " + MAX_NAME_LENGTH + " characters");
    }
    return cleaned;
  }
}
