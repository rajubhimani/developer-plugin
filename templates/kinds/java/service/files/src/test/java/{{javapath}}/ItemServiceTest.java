package {{javapkg}};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import {{javapkg}}.adapter.InMemoryItemRepository;
import {{javapkg}}.domain.InvalidItemException;
import {{javapkg}}.service.ItemService;
import org.junit.jupiter.api.Test;

/** Rules and use cases without Spring: fast, and no framework needed. */
class ItemServiceTest {

  private final ItemService service = new ItemService(new InMemoryItemRepository());

  @Test
  void storesTrimmedNamesAndListsThem() {
    var created = service.create("  pen ");
    assertEquals("pen", created.name());
    assertEquals(1, service.list().size());
  }

  @Test
  void rejectsBlankAndTooLongNames() {
    assertThrows(InvalidItemException.class, () -> service.create("   "));
    assertThrows(InvalidItemException.class, () -> service.create(null));
    assertThrows(InvalidItemException.class, () -> service.create("x".repeat(101)));
  }
}
