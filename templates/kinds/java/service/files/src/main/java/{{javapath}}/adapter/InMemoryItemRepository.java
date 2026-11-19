package {{javapkg}}.adapter;

import {{javapkg}}.domain.Item;
import {{javapkg}}.service.ItemRepository;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Repository;

/** In-memory storage for the first run and tests. Replace with a database adapter. */
@Repository
public class InMemoryItemRepository implements ItemRepository {

  private final List<Item> items = new ArrayList<>();

  @Override
  public synchronized Item add(String name) {
    Item item = new Item(items.size() + 1L, name);
    items.add(item);
    return item;
  }

  @Override
  public synchronized List<Item> all() {
    return List.copyOf(items);
  }
}
