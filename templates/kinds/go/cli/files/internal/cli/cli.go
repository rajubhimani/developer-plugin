// Package cli parses arguments and runs the command. It takes its streams as
// parameters so tests need no terminal.
package cli

import (
	"flag"
	"fmt"
	"io"
	"strings"
)

// Exit codes scripts can rely on.
const (
	ExitOK    = 0
	ExitError = 1
	ExitUsage = 2
)

// Run executes the command with args (without the program name) and returns the exit
// code. Results go to stdout; messages for people go to stderr.
func Run(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("{{name}}", flag.ContinueOnError)
	fs.SetOutput(stderr)
	shout := fs.Bool("shout", false, "use capital letters")
	if err := fs.Parse(args); err != nil {
		return ExitUsage
	}
	if fs.NArg() != 1 {
		// A failed write to a closed stream has nowhere to be reported, so it is dropped.
		_, _ = fmt.Fprintln(stderr, "usage: {{name}} [--shout] <name>")
		return ExitUsage
	}
	text := "Hello, " + fs.Arg(0) + "!"
	if *shout {
		text = strings.ToUpper(text)
	}
	if _, err := fmt.Fprintln(stdout, text); err != nil {
		return ExitError
	}
	return ExitOK
}
