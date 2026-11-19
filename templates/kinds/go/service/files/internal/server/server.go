// Package server holds the HTTP handler and the start and stop logic.
package server

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"time"

	"{{module}}/internal/config"
)

// Handler returns the routes. Liveness says the process is up; readiness says it can
// take traffic (add checks for dependencies the service cannot work without).
func Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("ok"))
	})
	mux.HandleFunc("/readyz", func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("ready"))
	})
	return mux
}

// Run serves until ctx is cancelled, then drains in-flight requests within the
// shutdown timeout. Every timeout is set: the defaults of net/http are none.
func Run(ctx context.Context, logger *slog.Logger, cfg config.Config) error {
	srv := &http.Server{
		Addr:              cfg.Addr,
		Handler:           Handler(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	failed := make(chan error, 1)
	go func() {
		logger.Info("listening", "addr", cfg.Addr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			failed <- err
		}
		close(failed)
	}()
	select {
	case err := <-failed:
		return err
	case <-ctx.Done():
	}
	logger.Info("shutting down")
	shutdown, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer cancel()
	return srv.Shutdown(shutdown)
}
