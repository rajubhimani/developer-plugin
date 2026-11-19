package {{javapkg}}.service;

import {{javapkg}}.domain.Item;
import java.util.List;

/** What the service needs from storage. Adapters implement it. */
public interface ItemRepository {

  /**
   * Stores a new item.
   *
   * @param name the cleaned name
   * @return the stored item with its id
   */
  Item add(String name);

  /**
   * Returns every item.
   *
   * @return the items, oldest first
   */
  List<Item> all();
}
