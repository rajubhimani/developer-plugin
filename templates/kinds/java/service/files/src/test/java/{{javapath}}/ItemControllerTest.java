package {{javapkg}};

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import {{javapkg}}.adapter.InMemoryItemRepository;
import {{javapkg}}.service.ItemService;
import {{javapkg}}.web.ApiExceptionHandler;
import {{javapkg}}.web.ItemController;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

/** Routes and the error format, without starting the whole application. */
class ItemControllerTest {

  private final MockMvc mvc =
      MockMvcBuilders.standaloneSetup(
              new ItemController(new ItemService(new InMemoryItemRepository())))
          .setControllerAdvice(new ApiExceptionHandler())
          .build();

  @Test
  void createsThenListsItems() throws Exception {
    mvc.perform(
            post("/items").contentType(MediaType.APPLICATION_JSON).content("{\"name\":\"pen\"}"))
        .andExpect(status().isCreated())
        .andExpect(jsonPath("$.name").value("pen"));
    mvc.perform(get("/items"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$[0].name").value("pen"));
  }

  @Test
  void aRuleViolationIsAProblemResponse() throws Exception {
    mvc.perform(post("/items").contentType(MediaType.APPLICATION_JSON).content("{\"name\":\"  \"}"))
        .andExpect(status().isUnprocessableContent())
        .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON))
        .andExpect(jsonPath("$.title").value("Invalid item"));
  }
}
