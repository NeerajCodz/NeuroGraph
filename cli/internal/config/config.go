package config

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"time"
)

type AuthConfig struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresAt    int64  `json:"expires_at"`
}

type DefaultsConfig struct {
	Layer       string `json:"layer"`
	WorkspaceID string `json:"workspace_id"`
	Provider    string `json:"provider"`
	Model       string `json:"model"`
}

type Config struct {
	BackendURL string         `json:"backend_url"`
	MCPURL     string         `json:"mcp_url"`
	MCPAPIKey  string         `json:"mcp_api_key"`
	Auth       AuthConfig     `json:"auth"`
	Defaults   DefaultsConfig `json:"defaults"`
}

func Default() *Config {
	return &Config{
		BackendURL: "http://localhost:8000/api/v1",
		MCPURL:     "http://localhost:8000/api/v1/mcp",
		Defaults: DefaultsConfig{
			Layer:    "personal",
			Provider: "gemini",
			Model:    "gemini-2.0-flash",
		},
	}
}

func Path() (string, error) {
	if explicit := os.Getenv("NEUROGRAPH_CONFIG"); explicit != "" {
		return explicit, nil
	}

	if appData := os.Getenv("APPDATA"); appData != "" {
		return filepath.Join(appData, "neurograph", "config.json"), nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, ".neurograph", "config.json"), nil
}

func Load() (*Config, error) {
	path, err := Path()
	if err != nil {
		return nil, err
	}

	b, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			cfg := Default()
			if saveErr := Save(cfg); saveErr != nil {
				return nil, saveErr
			}
			return cfg, nil
		}
		return nil, err
	}

	cfg := Default()
	if err := json.Unmarshal(b, cfg); err != nil {
		return nil, err
	}

	if cfg.BackendURL == "" {
		cfg.BackendURL = "http://localhost:8000/api/v1"
	}
	if cfg.MCPURL == "" {
		cfg.MCPURL = "http://localhost:8000/api/v1/mcp"
	}
	if cfg.Defaults.Layer == "" {
		cfg.Defaults.Layer = "personal"
	}
	if cfg.Defaults.Provider == "" {
		cfg.Defaults.Provider = "gemini"
	}
	if cfg.Defaults.Model == "" {
		cfg.Defaults.Model = "gemini-2.0-flash"
	}

	return cfg, nil
}

func Save(cfg *Config) error {
	path, err := Path()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}

	b, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, b, 0o600)
}

func Reset() (*Config, error) {
	cfg := Default()
	return cfg, Save(cfg)
}

func (c *Config) SetTokens(accessToken, refreshToken string, expiresInSec int64) {
	c.Auth.AccessToken = accessToken
	c.Auth.RefreshToken = refreshToken
	if expiresInSec > 0 {
		c.Auth.ExpiresAt = time.Now().Unix() + expiresInSec
		return
	}
	c.Auth.ExpiresAt = 0
}

func (c *Config) ClearTokens() {
	c.Auth.AccessToken = ""
	c.Auth.RefreshToken = ""
	c.Auth.ExpiresAt = 0
}

func (c *Config) IsLoggedIn() bool {
	if c.Auth.AccessToken == "" {
		return false
	}
	if c.Auth.ExpiresAt == 0 {
		return true
	}
	return time.Now().Unix() < c.Auth.ExpiresAt
}
