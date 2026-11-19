package cli

import (
	"bytes"
	"testing"
)

func run(args ...string) (int, string, string) {
	var out, errs bytes.Buffer
	code := Run(args, &out, &errs)
	return code, out.String(), errs.String()
}

func TestGreets(t *testing.T) {
	code, out, _ := run("world")
	if code != ExitOK || out != "Hello, world!\n" {
		t.Fatalf("code=%d out=%q", code, out)
	}
}

func TestShout(t *testing.T) {
	if _, out, _ := run("--shout", "world"); out != "HELLO, WORLD!\n" {
		t.Fatalf("out=%q", out)
	}
}

func TestMissingArgumentIsAUsageError(t *testing.T) {
	code, _, errs := run()
	if code != ExitUsage || errs == "" {
		t.Fatalf("code=%d errs=%q", code, errs)
	}
}
