package commands

import (
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
}

func loadRuntime() (*runtime, error) {
	cfg, err := config.Load()
	if err != nil {
		return nil, err
	}
	return &runtime{cfg: cfg, client: api.NewClient(cfg)}, nil
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
