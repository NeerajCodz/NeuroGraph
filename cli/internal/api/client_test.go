package api

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"neurograph/cli/internal/config"
)

func testClient(baseURL string) *Client {
	cfg := config.Default()
	cfg.BackendURL = baseURL
	cfg.MCPURL = baseURL + "/mcp"
	cfg.Auth.AccessToken = "token-123"
	cfg.Auth.RefreshToken = "refresh-123"
	cfg.MCPAPIKey = "api-key-xyz"
	return NewClient(cfg)
}

func TestGetIncludesAuthAndDecodesJSON(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Fatalf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/items" {
			t.Fatalf("expected /items, got %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer token-123" {
			t.Fatalf("missing auth header: %q", got)
		}
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	var out map[string]any
	if err := c.Get(context.Background(), "/items", &out); err != nil {
		t.Fatalf("get failed: %v", err)
	}
	if out["ok"] != true {
		t.Fatalf("unexpected response: %#v", out)
	}
}

func TestAPIErrorFromJSONDetail(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"detail":"bad request"}`))
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	err := c.Get(context.Background(), "/fail", nil)
	if err == nil {
		t.Fatalf("expected error")
	}
	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected APIError, got %T", err)
	}
	if apiErr.Status != http.StatusBadRequest || apiErr.Detail != "bad request" {
		t.Fatalf("unexpected api error: %+v", apiErr)
	}
}

func TestDeleteHandlesEmptyBody(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	if err := c.Delete(context.Background(), "/items/1", nil); err != nil {
		t.Fatalf("delete failed: %v", err)
	}
}

func TestLoginUsesFormEncoding(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/auth/login" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if ct := r.Header.Get("Content-Type"); !strings.Contains(ct, "application/x-www-form-urlencoded") {
			t.Fatalf("unexpected content type: %s", ct)
		}
		body, _ := io.ReadAll(r.Body)
		values, _ := url.ParseQuery(string(body))
		if values.Get("username") != "user@example.com" || values.Get("password") != "secret" {
			t.Fatalf("unexpected form payload: %s", string(body))
		}
		_, _ = w.Write([]byte(`{"access_token":"a","refresh_token":"r","expires_in":3600}`))
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	out, err := c.Login(context.Background(), "user@example.com", "secret")
	if err != nil {
		t.Fatalf("login failed: %v", err)
	}
	if out["access_token"] != "a" || out["refresh_token"] != "r" {
		t.Fatalf("unexpected login output: %#v", out)
	}
}

func TestRefreshNoAuthHeader(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/auth/refresh" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "" {
			t.Fatalf("refresh should not include auth header, got %q", got)
		}
		var payload map[string]string
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Fatalf("decode payload: %v", err)
		}
		if payload["refresh_token"] != "refresh-123" {
			t.Fatalf("unexpected refresh token: %#v", payload)
		}
		_, _ = w.Write([]byte(`{"access_token":"a2","refresh_token":"r2","expires_in":3600}`))
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	out, err := c.Refresh(context.Background())
	if err != nil {
		t.Fatalf("refresh failed: %v", err)
	}
	if out["access_token"] != "a2" || out["refresh_token"] != "r2" {
		t.Fatalf("unexpected refresh output: %#v", out)
	}
}

func TestMCPInvokeAndAPIKeyInvoke(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/mcp/invoke":
			if got := r.Header.Get("Authorization"); got != "Bearer token-123" {
				t.Fatalf("expected JWT auth header, got %q", got)
			}
		case "/mcp/invoke/api-key":
			if got := r.Header.Get("X-API-Key"); got != "api-key-xyz" {
				t.Fatalf("expected API key header, got %q", got)
			}
			if got := r.Header.Get("Authorization"); got != "" {
				t.Fatalf("api key invoke should not include auth header, got %q", got)
			}
		default:
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		_, _ = w.Write([]byte(`{"jsonrpc":"2.0","id":"cli-1","result":{"ok":true}}`))
	}))
	defer srv.Close()

	c := testClient(srv.URL)
	var out map[string]any
	if err := c.MCPInvoke(context.Background(), "tools/call", map[string]any{"name": "neurograph_status"}, &out); err != nil {
		t.Fatalf("mcp invoke failed: %v", err)
	}
	if err := c.MCPInvokeAPIKey(context.Background(), "tools/call", map[string]any{"name": "neurograph_status"}, &out); err != nil {
		t.Fatalf("mcp api-key invoke failed: %v", err)
	}
}
