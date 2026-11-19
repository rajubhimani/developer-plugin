package {{gopkg}}_test

import (
	"fmt"

	"{{module}}"
)

func ExampleGreet() {
	greeting, _ := {{gopkg}}.Greet("world")
	fmt.Println(greeting)
	// Output: Hello, world!
}
