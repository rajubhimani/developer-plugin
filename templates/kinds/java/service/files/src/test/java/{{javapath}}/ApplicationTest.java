package {{javapkg}};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

/** Starts the real application and calls the probes the orchestrator calls. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ApplicationTest {

  @Value("${local.server.port}")
  private int port;

  private HttpResponse<String> get(String path) throws Exception {
    HttpRequest request =
        HttpRequest.newBuilder(URI.create("http://localhost:" + port + path)).build();
    return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
  }

  @Test
  void livenessAndReadinessProbesAnswer() throws Exception {
    assertEquals(200, get("/actuator/health/liveness").statusCode());
    HttpResponse<String> readiness = get("/actuator/health/readiness");
    assertEquals(200, readiness.statusCode());
    assertTrue(readiness.body().contains("UP"));
  }

  @Test
  void nothingBeyondHealthIsExposed() throws Exception {
    assertEquals(404, get("/actuator/env").statusCode());
  }
}
