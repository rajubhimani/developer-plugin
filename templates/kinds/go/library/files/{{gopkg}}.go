package {{gopkg}}

import (
	"errors"
	"strings"
)

// ErrEmptyName is returned by Greet when the name is blank.
var ErrEmptyName = errors.New("name must not be empty")

// Greet returns a greeting for name. Replace with the library's real behaviour.
func Greet(name string) (string, error) {
	if strings.TrimSpace(name) == "" {
		return "", ErrEmptyName
	}
	return "Hello, " + name + "!", nil
}
