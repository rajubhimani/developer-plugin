package {{javapkg}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point. Spring wires the layers by scanning this package and its sub-packages. */
@SpringBootApplication
public class Application {

  /**
   * Starts the service.
   *
   * @param args the command line arguments
   */
  public static void main(String[] args) {
    SpringApplication.run(Application.class, args);
  }
}
