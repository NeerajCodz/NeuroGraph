package commands

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"neurograph/cli/internal/api"
	"neurograph/cli/internal/config"
)

type runtime struct {
	cfg    *config.Config
	client *api.Client
	useMCP bool
}

var globalMCPMode bool

func setMCPMode(enabled bool) {
	globalMCPMode = enabled
}

func loadRuntime() (*runtime, error) {
	cfg, err := config.Load()
	if err != nil {
		return nil, err
	}
	return &runtime{cfg: cfg, client: api.NewClient(cfg), useMCP: globalMCPMode}, nil
}

func requireLogin(rt *runtime) error {
	if rt == nil || rt.cfg == nil {
		return errors.New("runtime not initialized")
	}
	if !rt.cfg.IsLoggedIn() {
		return errors.New("not logged in; run neurograph auth login")
	}
	return nil
}

func toString(v any) string {
	switch t := v.(type) {
	case nil:
		return ""
	case string:
		return t
	case fmt.Stringer:
		return t.String()
	case float64:
		return strconv.FormatFloat(t, 'f', -1, 64)
	case bool:
		if t {
			return "true"
		}
		return "false"
	default:
		return fmt.Sprintf("%v", v)
	}
}

func toInt64(v any) int64 {
	switch t := v.(type) {
	case int:
		return int64(t)
	case int64:
		return t
	case float64:
		return int64(t)
	case string:
		i, _ := strconv.ParseInt(t, 10, 64)
		return i
	default:
		return 0
	}
}

func toBool(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case string:
		b, _ := strconv.ParseBool(t)
		return b
	case float64:
		return t != 0
	default:
		return false
	}
}

func splitCSV(in string) []string {
	parts := strings.Split(in, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func mapLayer(layer string) string {
	l := normalizeLayer(layer)
	if l == "workspace" {
		return "tenant"
	}
	return l
}

func mapChatLayer(layer string) string {
	l := normalizeLayer(layer)
	if l == "tenant" {
		return "workspace"
	}
	return l
}

func normalizeLayer(layer string) string {
	return strings.ToLower(strings.TrimSpace(layer))
}

func saveRuntime(rt *runtime) error {
	if rt == nil || rt.cfg == nil {
		return errors.New("runtime not initialized")
	}
	return config.Save(rt.cfg)
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if strings.TrimSpace(v) != "" {
			return strings.TrimSpace(v)
		}
	}
	return ""
}

func contains(items []string, needle string) bool {
	for _, item := range items {
		if item == needle {
			return true
		}
	}
	return false
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	if len(s) <= n {
		return s
	}
	return s[:n-3] + "..."
}

func mcpInvokeText(ctx context.Context, rt *runtime, toolName string, arguments map[string]any) (string, error) {
	if rt == nil || rt.client == nil {
		return "", errors.New("runtime not initialized")
	}
	if strings.TrimSpace(toolName) == "" {
		return "", errors.New("tool name required")
	}

	params := map[string]any{
		"name":      strings.TrimSpace(toolName),
		"arguments": arguments,
	}
	var resp map[string]any
	if err := rt.client.MCPInvoke(ctx, "tools/call", params, &resp); err != nil {
		return "", err
	}

	if errObj, ok := resp["error"].(map[string]any); ok {
		message := firstNonEmpty(toString(errObj["message"]), "mcp tool call failed")
		return "", errors.New(message)
	}

	resultObj, ok := resp["result"].(map[string]any)
	if !ok {
		return "", errors.New("invalid mcp response payload")
	}
	contentArr, ok := resultObj["content"].([]any)
	if !ok || len(contentArr) == 0 {
		return "", errors.New("mcp response missing content")
	}
	contentItem, ok := contentArr[0].(map[string]any)
	if !ok {
		return "", errors.New("invalid mcp content payload")
	}

	return toString(contentItem["text"]), nil
}

func mcpInvokeJSON(ctx context.Context, rt *runtime, toolName string, arguments map[string]any, out any) error {
	text, err := mcpInvokeText(ctx, rt, toolName, arguments)
	if err != nil {
		return err
	}

	raw := strings.TrimSpace(text)
	if strings.HasPrefix(strings.ToLower(raw), "error:") {
		msg := strings.TrimSpace(strings.TrimPrefix(raw, "Error:"))
		if msg == "" {
			msg = raw
		}
		return errors.New(msg)
	}
	if out == nil {
		return nil
	}
	if err := json.Unmarshal([]byte(raw), out); err != nil {
		return fmt.Errorf("failed to parse mcp json response: %w", err)
	}
	return nil
}
