// Command {{name}} <one line: what this command does>.
package main

import (
	"os"

	"{{module}}/internal/cli"
)

func main() {
	os.Exit(cli.Run(os.Args[1:], os.Stdout, os.Stderr))
}
