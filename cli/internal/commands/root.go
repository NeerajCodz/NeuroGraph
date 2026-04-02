package commands

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func NewRootCmd() *cobra.Command {
	var mcpMode bool
	root := &cobra.Command{
		Use:   "neurograph",
		Short: "NeuroGraph CLI",
		Long:  "NeuroGraph CLI client for backend and MCP servers.",
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			setMCPMode(mcpMode)
		},
	}
	root.PersistentFlags().BoolVar(&mcpMode, "mcp", false, "Route supported commands through MCP tools")

	root.AddCommand(newStatusCmd())
	root.AddCommand(newAuthCmd())
	root.AddCommand(newConfigCmd())
	root.AddCommand(newMemoryCmd())
	root.AddCommand(newChatCmd())
	root.AddCommand(newConversationsCmd())
	root.AddCommand(newWorkspacesCmd())
	root.AddCommand(newGraphCmd())
	root.AddCommand(newModelsCmd())
	root.AddCommand(newIntegrationsCmd())
	root.AddCommand(newProfileCmd())
	root.AddCommand(newMCPCmd())

	root.AddCommand(newQuickAskCmd())
	root.AddCommand(newQuickRememberCmd())
	root.AddCommand(newQuickRecallCmd())

	return root
}

func newStatusCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show CLI status",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			output.Heading("NeuroGraph CLI Status")
			output.KV("Backend URL", rt.cfg.BackendURL)
			output.KV("MCP URL", rt.cfg.MCPURL)
			output.KV("Logged In", rt.cfg.IsLoggedIn())
			output.KV("Default Layer", rt.cfg.Defaults.Layer)
			output.KV("Default Provider", rt.cfg.Defaults.Provider)
			output.KV("Default Model", rt.cfg.Defaults.Model)
			output.KV("Workspace", rt.cfg.Defaults.WorkspaceID)
			return nil
		},
	}
}

func newQuickAskCmd() *cobra.Command {
	var provider string
	var model string
	var includeGlobal bool
	var workspaceID string
	var layer string

	cmd := &cobra.Command{
		Use:   "ask [message]",
		Short: "Quick chat (alias of chat send)",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			chatLayer := mapChatLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			if chatLayer == "workspace" && ws == "" {
				return fmt.Errorf("workspace_id required for workspace layer; run neurograph config set workspace_id <uuid>")
			}

			if rt.useMCP {
				argsMap := map[string]any{
					"message":         strings.Join(args, " "),
					"layer":           chatLayer,
					"include_global":  includeGlobal,
					"response_format": "json",
					"use_memory":      true,
				}
				if ws != "" {
					argsMap["workspace_id"] = ws
				}
				if p := providerOrDefault(provider, rt.cfg.Defaults.Provider); p != "" {
					argsMap["provider"] = p
				}
				if m := modelOrDefault(model, rt.cfg.Defaults.Model); m != "" {
					argsMap["model"] = m
				}

				var resp map[string]any
				if err := mcpInvokeJSON(context.Background(), rt, "neurograph_chat", argsMap, &resp); err != nil {
					return err
				}
				fmt.Println(toString(resp["content"]))
				return nil
			}

			payload := map[string]any{
				"content":        strings.Join(args, " "),
				"workspace_id":   ws,
				"layer":          chatLayer,
				"include_global": includeGlobal,
				"provider":       providerOrDefault(provider, rt.cfg.Defaults.Provider),
				"model":          modelOrDefault(model, rt.cfg.Defaults.Model),
				"agents_enabled": true,
			}
			if payload["workspace_id"] == "" {
				delete(payload, "workspace_id")
			}

			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/chat/message", payload, &resp); err != nil {
				return err
			}
			fmt.Println(toString(resp["content"]))
			return nil
		},
	}

	cmd.Flags().StringVar(&provider, "provider", "", "LLM provider")
	cmd.Flags().StringVar(&model, "model", "", "Model ID")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace|global")
	cmd.Flags().BoolVar(&includeGlobal, "global", false, "Include global memory")
	return cmd
}

func newQuickRememberCmd() *cobra.Command {
	var layer string
	cmd := &cobra.Command{
		Use:   "remember [content]",
		Short: "Quick memory store (alias of memory remember)",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			mapped := mapLayer(layer)
			if mapped == "" {
				mapped = mapLayer(rt.cfg.Defaults.Layer)
			}
			ws := rt.cfg.Defaults.WorkspaceID

			if rt.useMCP {
				argsMap := map[string]any{
					"content":         strings.Join(args, " "),
					"layer":           mapped,
					"response_format": "json",
				}
				if mapped == "tenant" {
					if ws == "" {
						return fmt.Errorf("workspace_id required for workspace layer; run neurograph config set workspace_id <uuid>")
					}
					argsMap["workspace_id"] = ws
				}

				var resp map[string]any
				if err := mcpInvokeJSON(context.Background(), rt, "neurograph_remember", argsMap, &resp); err != nil {
					return err
				}
				output.Success("Memory stored")
				output.KV("ID", toString(resp["id"]))
				return nil
			}

			payload := map[string]any{
				"content": strings.Join(args, " "),
				"layer":   mapped,
			}
			if mapped == "tenant" {
				if ws == "" {
					return fmt.Errorf("workspace_id required for workspace layer; run neurograph config set workspace_id <uuid>")
				}
				payload["workspace_id"] = ws
				payload["tenant_id"] = ws
			}

			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/memory/remember", payload, &resp); err != nil {
				return err
			}
			output.Success("Memory stored")
			output.KV("ID", toString(resp["id"]))
			return nil
		},
	}
	cmd.Flags().StringVar(&layer, "layer", "", "Layer: personal|workspace|global")
	return cmd
}

func newQuickRecallCmd() *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use:   "recall [query]",
		Short: "Quick memory recall (alias of memory recall)",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			layers := []string{mapLayer(rt.cfg.Defaults.Layer)}
			if rt.useMCP {
				argsMap := map[string]any{
					"query":           strings.Join(args, " "),
					"max_results":     limit,
					"layers":          layers,
					"response_format": "json",
				}
				if layers[0] == "tenant" {
					if rt.cfg.Defaults.WorkspaceID == "" {
						return fmt.Errorf("workspace_id required for workspace layer; run neurograph config set workspace_id <uuid>")
					}
					argsMap["workspace_id"] = rt.cfg.Defaults.WorkspaceID
				}

				var resp []map[string]any
				if err := mcpInvokeJSON(context.Background(), rt, "neurograph_recall", argsMap, &resp); err != nil {
					return err
				}
				for i, m := range resp {
					output.Heading(fmt.Sprintf("Result %d", i+1))
					output.KV("ID", toString(m["id"]))
					output.KV("Layer", toString(m["layer"]))
					output.KV("Score", toString(m["score"]))
					fmt.Println(toString(m["content"]))
				}
				if len(resp) == 0 {
					output.Info("No memory found")
				}
				return nil
			}

			payload := map[string]any{
				"query":       strings.Join(args, " "),
				"max_results": limit,
				"layers":      layers,
			}
			if layers[0] == "tenant" {
				if rt.cfg.Defaults.WorkspaceID == "" {
					return fmt.Errorf("workspace_id required for workspace layer; run neurograph config set workspace_id <uuid>")
				}
				payload["workspace_id"] = rt.cfg.Defaults.WorkspaceID
			}

			var resp []map[string]any
			if err := rt.client.Post(context.Background(), "/memory/recall", payload, &resp); err != nil {
				return err
			}
			for i, m := range resp {
				output.Heading(fmt.Sprintf("Result %d", i+1))
				output.KV("ID", toString(m["id"]))
				output.KV("Layer", toString(m["layer"]))
				output.KV("Score", toString(m["score"]))
				fmt.Println(toString(m["content"]))
			}
			if len(resp) == 0 {
				output.Info("No memory found")
			}
			return nil
		},
	}
	cmd.Flags().IntVar(&limit, "limit", 5, "Max results")
	return cmd
}

func providerOrDefault(v, d string) string {
	if strings.TrimSpace(v) == "" {
		return d
	}
	return v
}

func modelOrDefault(v, d string) string {
	if strings.TrimSpace(v) == "" {
		return d
	}
	return v
}
