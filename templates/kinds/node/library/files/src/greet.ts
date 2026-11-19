/** Return a greeting for `name`. Replace with the library's real behaviour. */
export function greet(name: string): string {
  if (name.trim() === "") throw new Error("name must not be empty");
  return `Hello, ${name}!`;
}
