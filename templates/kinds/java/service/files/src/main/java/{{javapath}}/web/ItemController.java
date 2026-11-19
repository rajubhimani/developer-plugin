package {{javapkg}}.web;

import {{javapkg}}.domain.Item;
import {{javapkg}}.service.ItemService;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Item routes. Thin: parse the request, call the service, shape the response. */
@RestController
@RequestMapping("/items")
public class ItemController {

  /**
   * The request body for creating an item.
   *
   * @param name the item's name
   */
  public record ItemRequest(String name) {}

  /**
   * An item as the API returns it. Separate from the domain type on purpose.
   *
   * @param id the identifier
   * @param name the name
   */
  public record ItemResponse(long id, String name) {
    static ItemResponse of(Item item) {
      return new ItemResponse(item.id(), item.name());
    }
  }

  private final ItemService service;

  /**
   * Creates the controller.
   *
   * @param service the use cases
   */
  public ItemController(ItemService service) {
    this.service = service;
  }

  /**
   * Creates an item.
   *
   * @param request the body
   * @return the stored item
   */
  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ItemResponse create(@RequestBody ItemRequest request) {
    return ItemResponse.of(service.create(request.name()));
  }

  /**
   * Lists items.
   *
   * @return all items
   */
  @GetMapping
  public List<ItemResponse> list() {
    return service.list().stream().map(ItemResponse::of).toList();
  }
}
