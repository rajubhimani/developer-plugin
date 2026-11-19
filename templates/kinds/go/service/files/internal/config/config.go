// Package config reads settings from the environment, once, at start-up.
package config

import (
	"fmt"
	"strconv"
	"time"
)

// Config holds every setting the service reads. Names are APP_* environment variables.
type Config struct {
	Addr            string        // APP_ADDR, default ":8080"
	ShutdownTimeout time.Duration // APP_SHUTDOWN_TIMEOUT_SECONDS, default 20
}

// Load reads the settings through getenv (os.Getenv in main, a map in tests) and fails
// with the setting's name when a value is invalid.
func Load(getenv func(string) string) (Config, error) {
	cfg := Config{Addr: ":8080", ShutdownTimeout: 20 * time.Second}
	if v := getenv("APP_ADDR"); v != "" {
		cfg.Addr = v
	}
	if v := getenv("APP_SHUTDOWN_TIMEOUT_SECONDS"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n <= 0 {
			return Config{}, fmt.Errorf("APP_SHUTDOWN_TIMEOUT_SECONDS must be a positive whole number, got %q", v)
		}
		cfg.ShutdownTimeout = time.Duration(n) * time.Second
	}
	return cfg, nil
}
