package commands

import (
	"errors"
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/config"
	"neurograph/cli/internal/output"
)

func newConfigCmd() *cobra.Command {
	cfgCmd := &cobra.Command{Use: "config", Short: "Manage CLI config"}
	cfgCmd.AddCommand(newConfigShowCmd())
	cfgCmd.AddCommand(newConfigSetCmd())
	cfgCmd.AddCommand(newConfigGetCmd())
	cfgCmd.AddCommand(newConfigResetCmd())
	cfgCmd.AddCommand(newConfigPathCmd())
	return cfgCmd
}

func newConfigShowCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "show",
		Short: "Show config",
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load()
			if err != nil {
				return err
			}
			if jsonOut {
				safe := *cfg
				safe.Auth.AccessToken = maskToken(safe.Auth.AccessToken)
				safe.Auth.RefreshToken = maskToken(safe.Auth.RefreshToken)
				safe.MCPAPIKey = maskToken(safe.MCPAPIKey)
				return output.JSON(safe)
			}
			output.Heading("NeuroGraph Config")
			output.KV("Backend URL", cfg.BackendURL)
			output.KV("MCP URL", cfg.MCPURL)
			output.KV("MCP API Key", maskToken(cfg.MCPAPIKey))
			output.KV("Default Layer", cfg.Defaults.Layer)
			output.KV("Default Workspace", cfg.Defaults.WorkspaceID)
			output.KV("Default Provider", cfg.Defaults.Provider)
			output.KV("Default Model", cfg.Defaults.Model)
			output.KV("Logged In", cfg.IsLoggedIn())
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newConfigSetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "set <key> <value>",
		Short: "Set config value",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load()
			if err != nil {
				return err
			}
			k := strings.ToLower(strings.TrimSpace(args[0]))
			v := args[1]
			switch k {
			case "backend_url", "backend", "api_url":
				cfg.BackendURL = strings.TrimRight(v, "/")
			case "mcp_url", "mcp":
				cfg.MCPURL = strings.TrimRight(v, "/")
			case "mcp_api_key", "mcp_key":
				cfg.MCPAPIKey = strings.TrimSpace(v)
			case "layer", "default_layer":
				layer := mapLayer(v)
				if layer != "personal" && layer != "tenant" && layer != "global" {
					return errors.New("layer must be personal|workspace|global")
				}
				cfg.Defaults.Layer = layer
			case "workspace", "workspace_id":
				cfg.Defaults.WorkspaceID = strings.TrimSpace(v)
			case "provider":
				cfg.Defaults.Provider = strings.TrimSpace(v)
			case "model":
				cfg.Defaults.Model = strings.TrimSpace(v)
			default:
				return fmt.Errorf("unsupported key: %s", k)
			}
			if err := config.Save(cfg); err != nil {
				return err
			}
			output.Success("Config updated")
			return nil
		},
	}
}

func newConfigGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <key>",
		Short: "Get config value",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load()
			if err != nil {
				return err
			}
			switch strings.ToLower(args[0]) {
			case "backend_url", "backend", "api_url":
				fmt.Println(cfg.BackendURL)
			case "mcp_url", "mcp":
				fmt.Println(cfg.MCPURL)
			case "mcp_api_key", "mcp_key":
				fmt.Println(maskToken(cfg.MCPAPIKey))
			case "layer", "default_layer":
				fmt.Println(cfg.Defaults.Layer)
			case "workspace", "workspace_id":
				fmt.Println(cfg.Defaults.WorkspaceID)
			case "provider":
				fmt.Println(cfg.Defaults.Provider)
			case "model":
				fmt.Println(cfg.Defaults.Model)
			default:
				return fmt.Errorf("unsupported key: %s", args[0])
			}
			return nil
		},
	}
}

func newConfigResetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "reset",
		Short: "Reset config to defaults",
		RunE: func(cmd *cobra.Command, args []string) error {
			_, err := config.Reset()
			if err != nil {
				return err
			}
			output.Success("Config reset")
			return nil
		},
	}
}

func newConfigPathCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "path",
		Short: "Show config file path",
		RunE: func(cmd *cobra.Command, args []string) error {
			p, err := config.Path()
			if err != nil {
				return err
			}
			fmt.Println(p)
			return nil
		},
	}
}

func maskToken(v string) string {
	if strings.TrimSpace(v) == "" {
		return ""
	}
	if len(v) <= 8 {
		return "********"
	}
	return v[:4] + "..." + v[len(v)-4:]
}
