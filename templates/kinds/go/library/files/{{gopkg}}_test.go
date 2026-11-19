package {{gopkg}}

import (
	"errors"
	"testing"
)

func TestGreet(t *testing.T) {
	got, err := Greet("world")
	if err != nil || got != "Hello, world!" {
		t.Fatalf("Greet = %q, %v", got, err)
	}
}

func TestGreetRejectsABlankName(t *testing.T) {
	if _, err := Greet("  "); !errors.Is(err, ErrEmptyName) {
		t.Fatalf("want ErrEmptyName, got %v", err)
	}
}
