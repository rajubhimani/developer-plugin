package {{javapkg}}.web;

import {{javapkg}}.domain.InvalidItemException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Turns domain exceptions into problem-details responses (no stack traces, no internals). */
@RestControllerAdvice
public class ApiExceptionHandler {

  /**
   * Maps a broken business rule to a 422 problem response.
   *
   * @param exception the broken rule
   * @return the problem details
   */
  @ExceptionHandler(InvalidItemException.class)
  public ProblemDetail invalidItem(InvalidItemException exception) {
    ProblemDetail problem =
        ProblemDetail.forStatusAndDetail(HttpStatus.UNPROCESSABLE_CONTENT, exception.getMessage());
    problem.setTitle("Invalid item");
    return problem;
  }
}
