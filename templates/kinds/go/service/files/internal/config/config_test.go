package config

import (
	"strings"
	"testing"
	"time"
)

func env(values map[string]string) func(string) string {
	return func(key string) string { return values[key] }
}

func TestLoadDefaults(t *testing.T) {
	cfg, err := Load(env(nil))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Addr != ":8080" || cfg.ShutdownTimeout != 20*time.Second {
		t.Fatalf("unexpected defaults: %+v", cfg)
	}
}

func TestLoadOverrides(t *testing.T) {
	cfg, err := Load(env(map[string]string{"APP_ADDR": ":9000", "APP_SHUTDOWN_TIMEOUT_SECONDS": "5"}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Addr != ":9000" || cfg.ShutdownTimeout != 5*time.Second {
		t.Fatalf("unexpected config: %+v", cfg)
	}
}

func TestLoadRejectsABadValueByName(t *testing.T) {
	_, err := Load(env(map[string]string{"APP_SHUTDOWN_TIMEOUT_SECONDS": "soon"}))
	if err == nil || !strings.Contains(err.Error(), "APP_SHUTDOWN_TIMEOUT_SECONDS") {
		t.Fatalf("want an error naming the setting, got %v", err)
	}
}
