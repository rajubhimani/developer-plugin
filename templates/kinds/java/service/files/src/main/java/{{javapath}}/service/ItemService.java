package {{javapkg}}.service;

import {{javapkg}}.domain.Item;
import java.util.List;
import org.springframework.stereotype.Service;

/** Use cases for items. Knows nothing about HTTP or concrete storage. */
@Service
public class ItemService {

  private final ItemRepository repository;

  /**
   * Creates the service.
   *
   * @param repository the storage port
   */
  public ItemService(ItemRepository repository) {
    this.repository = repository;
  }

  /**
   * Validates and stores a new item.
   *
   * @param name the raw name
   * @return the stored item
   */
  public Item create(String name) {
    return repository.add(Item.cleanName(name));
  }

  /**
   * Returns all items.
   *
   * @return the items
   */
  public List<Item> list() {
    return repository.all();
  }
}
