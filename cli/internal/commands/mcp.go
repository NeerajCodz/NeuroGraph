package commands

import (
	"context"
	"errors"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newMCPCmd() *cobra.Command {
	mcp := &cobra.Command{Use: "mcp", Short: "MCP routes"}
	mcp.AddCommand(newMCPToolsCmd())
	mcp.AddCommand(newMCPInvokeCmd())
	mcp.AddCommand(newMCPInvokeAPIKeyCmd())
	return mcp
}

func newMCPToolsCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "tools",
		Short: "List available MCP tools",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/mcp/tools", &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMCPInvokeCmd() *cobra.Command {
	var toolName string
	var jsonOut bool
	var query string
	var content string
	var layer string
	var workspaceID string
	var responseFormat string
	var maxResults int

	cmd := &cobra.Command{
		Use:   "invoke",
		Short: "Invoke MCP tool via JWT auth",
		RunE: func(cmd *cobra.Command, args []string) error {
			if toolName == "" {
				return errors.New("--tool is required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			arguments := map[string]any{}
			switch toolName {
			case "neurograph_remember":
				if content == "" {
					return errors.New("--content is required for neurograph_remember")
				}
				arguments["content"] = content
				arguments["layer"] = firstNonEmpty(layer, rt.cfg.Defaults.Layer)
				if ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID); ws != "" {
					arguments["workspace_id"] = ws
				}
				arguments["response_format"] = firstNonEmpty(responseFormat, "json")
			case "neurograph_recall":
				if query == "" {
					return errors.New("--query is required for neurograph_recall")
				}
				arguments["query"] = query
				arguments["max_results"] = maxResults
				arguments["layers"] = []string{mapLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))}
				if ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID); ws != "" {
					arguments["workspace_id"] = ws
				}
				arguments["response_format"] = firstNonEmpty(responseFormat, "json")
			default:
				if query != "" {
					arguments["query"] = query
				}
				if content != "" {
					arguments["content"] = content
				}
				if layer != "" {
					arguments["layer"] = layer
				}
				if ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID); ws != "" {
					arguments["workspace_id"] = ws
				}
				if responseFormat != "" {
					arguments["response_format"] = responseFormat
				}
			}

			params := map[string]any{"name": toolName, "arguments": arguments}
			var resp map[string]any
			if err := rt.client.MCPInvoke(context.Background(), "tools/call", params, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&toolName, "tool", "", "Tool name")
	cmd.Flags().StringVar(&query, "query", "", "Query argument")
	cmd.Flags().StringVar(&content, "content", "", "Content argument")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer argument")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace argument")
	cmd.Flags().StringVar(&responseFormat, "response-format", "json", "Response format markdown|json")
	cmd.Flags().IntVar(&maxResults, "max-results", 10, "Max results")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMCPInvokeAPIKeyCmd() *cobra.Command {
	var toolName string
	var query string
	var content string
	var layer string
	var workspaceID string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "invoke-api-key",
		Short: "Invoke MCP tool via API key",
		RunE: func(cmd *cobra.Command, args []string) error {
			if toolName == "" {
				return errors.New("--tool is required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if rt.cfg.MCPAPIKey == "" {
				return errors.New("mcp_api_key not set; run neurograph config set mcp_api_key <key>")
			}

			arguments := map[string]any{}
			if query != "" {
				arguments["query"] = query
			}
			if content != "" {
				arguments["content"] = content
			}
			if layer != "" {
				arguments["layer"] = layer
			}
			if workspaceID != "" {
				arguments["workspace_id"] = workspaceID
			}

			params := map[string]any{"name": toolName, "arguments": arguments}
			var resp map[string]any
			if err := rt.client.MCPInvokeAPIKey(context.Background(), "tools/call", params, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&toolName, "tool", "", "Tool name")
	cmd.Flags().StringVar(&query, "query", "", "Query argument")
	cmd.Flags().StringVar(&content, "content", "", "Content argument")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer argument")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace argument")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}
