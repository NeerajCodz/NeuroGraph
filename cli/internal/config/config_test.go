package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDefaultConfigValues(t *testing.T) {
	cfg := Default()
	if cfg.BackendURL != "http://localhost:8000/api/v1" {
		t.Fatalf("unexpected backend url: %s", cfg.BackendURL)
	}
	if cfg.MCPURL != "http://localhost:8000/api/v1/mcp" {
		t.Fatalf("unexpected mcp url: %s", cfg.MCPURL)
	}
	if cfg.Defaults.Layer != "personal" {
		t.Fatalf("unexpected default layer: %s", cfg.Defaults.Layer)
	}
}

func TestLoadSaveAndResetWithExplicitPath(t *testing.T) {
	tmp := t.TempDir()
	cfgPath := filepath.Join(tmp, "config.json")
	t.Setenv("NEUROGRAPH_CONFIG", cfgPath)

	cfg, err := Load()
	if err != nil {
		t.Fatalf("load default: %v", err)
	}

	cfg.BackendURL = "http://localhost:9000/api/v1"
	cfg.MCPAPIKey = "abc123"
	cfg.Defaults.Layer = "tenant"
	cfg.Defaults.WorkspaceID = "workspace-1"
	if err := Save(cfg); err != nil {
		t.Fatalf("save: %v", err)
	}

	reloaded, err := Load()
	if err != nil {
		t.Fatalf("reload: %v", err)
	}
	if reloaded.BackendURL != "http://localhost:9000/api/v1" {
		t.Fatalf("backend url not persisted: %s", reloaded.BackendURL)
	}
	if reloaded.MCPAPIKey != "abc123" {
		t.Fatalf("mcp api key not persisted: %s", reloaded.MCPAPIKey)
	}
	if reloaded.Defaults.Layer != "tenant" {
		t.Fatalf("layer not persisted: %s", reloaded.Defaults.Layer)
	}

	resetCfg, err := Reset()
	if err != nil {
		t.Fatalf("reset: %v", err)
	}
	if resetCfg.Defaults.Layer != "personal" {
		t.Fatalf("reset should restore defaults, got layer=%s", resetCfg.Defaults.Layer)
	}
}

func TestPathPrefersExplicitEnv(t *testing.T) {
	t.Setenv("NEUROGRAPH_CONFIG", `C:\temp\neurograph-config.json`)
	path, err := Path()
	if err != nil {
		t.Fatalf("path: %v", err)
	}
	if path != `C:\temp\neurograph-config.json` {
		t.Fatalf("unexpected path: %s", path)
	}
}

func TestSetTokensAndLoginState(t *testing.T) {
	cfg := Default()
	if cfg.IsLoggedIn() {
		t.Fatalf("should not be logged in initially")
	}

	cfg.SetTokens("access", "refresh", 60)
	if cfg.Auth.AccessToken != "access" || cfg.Auth.RefreshToken != "refresh" {
		t.Fatalf("tokens were not set")
	}
	if !cfg.IsLoggedIn() {
		t.Fatalf("expected logged in after token set")
	}

	cfg.SetTokens("access", "refresh", 1)
	time.Sleep(2 * time.Second)
	if cfg.IsLoggedIn() {
		t.Fatalf("expected token to expire")
	}

	cfg.SetTokens("access", "refresh", 0)
	if !cfg.IsLoggedIn() {
		t.Fatalf("token with no expiry should be treated as logged in")
	}

	cfg.ClearTokens()
	if cfg.IsLoggedIn() {
		t.Fatalf("expected logged out after clear")
	}
}

func TestLoadInvalidJSONReturnsError(t *testing.T) {
	tmp := t.TempDir()
	cfgPath := filepath.Join(tmp, "bad.json")
	if err := os.WriteFile(cfgPath, []byte("{not-json"), 0o600); err != nil {
		t.Fatalf("write invalid config: %v", err)
	}
	t.Setenv("NEUROGRAPH_CONFIG", cfgPath)

	if _, err := Load(); err == nil {
		t.Fatalf("expected load error for invalid json")
	}
}
