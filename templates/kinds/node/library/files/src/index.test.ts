import { describe, expect, test } from "vitest";
import { greet } from "./index.js";

describe("public API", () => {
  test("greet returns a greeting", () => {
    expect(greet("world")).toBe("Hello, world!");
  });

  test("greet rejects an empty name", () => {
    expect(() => greet("  ")).toThrow("must not be empty");
  });
});
