package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"neurograph/cli/internal/config"
)

type Client struct {
	httpClient *http.Client
	cfg        *config.Config
}

type APIError struct {
	Status int
	Detail string
}

func (e *APIError) Error() string {
	if e.Detail == "" {
		return fmt.Sprintf("API request failed with status %d", e.Status)
	}
	return e.Detail
}

func NewClient(cfg *config.Config) *Client {
	return &Client{
		httpClient: &http.Client{Timeout: 60 * time.Second},
		cfg:        cfg,
	}
}

func (c *Client) doJSON(ctx context.Context, method, rawURL string, body any, withAuth bool) ([]byte, error) {
	return c.doJSONWithHeaders(ctx, method, rawURL, body, withAuth, nil)
}

func (c *Client) doJSONWithHeaders(
	ctx context.Context,
	method, rawURL string,
	body any,
	withAuth bool,
	extraHeaders map[string]string,
) ([]byte, error) {
	var reader io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(b)
	}

	req, err := http.NewRequestWithContext(ctx, method, rawURL, reader)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	if withAuth && c.cfg.Auth.AccessToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.cfg.Auth.AccessToken)
	}
	for k, v := range extraHeaders {
		req.Header.Set(k, v)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	payload, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		apiErr := &APIError{Status: resp.StatusCode}
		var errBody map[string]any
		if json.Unmarshal(payload, &errBody) == nil {
			if detail, ok := errBody["detail"].(string); ok {
				apiErr.Detail = detail
			}
		}
		if apiErr.Detail == "" {
			apiErr.Detail = strings.TrimSpace(string(payload))
		}
		return nil, apiErr
	}

	return payload, nil
}

func (c *Client) Get(ctx context.Context, path string, out any) error {
	b, err := c.doJSON(ctx, http.MethodGet, c.cfg.BackendURL+path, nil, true)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Client) Delete(ctx context.Context, path string, out any) error {
	b, err := c.doJSON(ctx, http.MethodDelete, c.cfg.BackendURL+path, nil, true)
	if err != nil {
		return err
	}
	if out == nil || len(b) == 0 {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Client) Post(ctx context.Context, path string, in any, out any) error {
	b, err := c.doJSON(ctx, http.MethodPost, c.cfg.BackendURL+path, in, true)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Client) Patch(ctx context.Context, path string, in any, out any) error {
	b, err := c.doJSON(ctx, http.MethodPatch, c.cfg.BackendURL+path, in, true)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Client) Login(ctx context.Context, email, password string) (map[string]any, error) {
	form := url.Values{}
	form.Set("username", email)
	form.Set("password", password)

	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.cfg.BackendURL+"/auth/login",
		strings.NewReader(form.Encode()),
	)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		apiErr := &APIError{Status: resp.StatusCode}
		var errBody map[string]any
		if json.Unmarshal(b, &errBody) == nil {
			if detail, ok := errBody["detail"].(string); ok {
				apiErr.Detail = detail
			}
		}
		if apiErr.Detail == "" {
			apiErr.Detail = strings.TrimSpace(string(b))
		}
		return nil, apiErr
	}

	var out map[string]any
	if err := json.Unmarshal(b, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func (c *Client) Refresh(ctx context.Context) (map[string]any, error) {
	payload := map[string]string{"refresh_token": c.cfg.Auth.RefreshToken}
	b, err := c.doJSON(ctx, http.MethodPost, c.cfg.BackendURL+"/auth/refresh", payload, false)
	if err != nil {
		return nil, err
	}
	var out map[string]any
	if err := json.Unmarshal(b, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func (c *Client) MCPInvoke(ctx context.Context, method string, params map[string]any, out any) error {
	payload := map[string]any{
		"jsonrpc": "2.0",
		"id":      "cli-1",
		"method":  method,
		"params":  params,
	}

	b, err := c.doJSON(ctx, http.MethodPost, c.cfg.MCPURL+"/invoke", payload, true)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Client) MCPInvokeAPIKey(ctx context.Context, method string, params map[string]any, out any) error {
	payload := map[string]any{
		"jsonrpc": "2.0",
		"id":      "cli-1",
		"method":  method,
		"params":  params,
	}
	headers := map[string]string{}
	if c.cfg.MCPAPIKey != "" {
		headers["X-API-Key"] = c.cfg.MCPAPIKey
	}
	b, err := c.doJSONWithHeaders(ctx, http.MethodPost, c.cfg.MCPURL+"/invoke/api-key", payload, false, headers)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}
