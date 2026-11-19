// Command {{name}} runs the service. Keep main thin: read configuration, wire the
// parts together and start. The logic lives in internal/.
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"{{module}}/internal/config"
	"{{module}}/internal/server"
)

func main() {
	if err := run(); err != nil {
		slog.Error("fatal", "error", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := config.Load(os.Getenv)
	if err != nil {
		return err
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	// SIGTERM is what a container platform sends: stop accepting, finish, exit.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	return server.Run(ctx, logger, cfg)
}
