package commands

import (
	"context"
	"errors"
	"fmt"
	"net/url"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newWorkspacesCmd() *cobra.Command {
	ws := &cobra.Command{Use: "workspaces", Short: "Workspace routes"}
	ws.AddCommand(newWorkspacesCreateCmd())
	ws.AddCommand(newWorkspacesListCmd())
	ws.AddCommand(newWorkspacesGetCmd())
	ws.AddCommand(newWorkspacesUpdateCmd())
	ws.AddCommand(newWorkspacesDeleteCmd())
	ws.AddCommand(newWorkspacesJoinCmd())
	ws.AddCommand(newWorkspacesMembersCmd())
	ws.AddCommand(newWorkspacesRegenerateTokenCmd())
	ws.AddCommand(newWorkspacesUseCmd())
	ws.AddCommand(newWorkspacesCurrentCmd())
	return ws
}

func newWorkspacesCreateCmd() *cobra.Command {
	var name string
	var description string
	var isPublic bool
	var memoryEnabled bool
	var defaultProvider string
	var defaultModel string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create workspace",
		RunE: func(cmd *cobra.Command, args []string) error {
			if name == "" {
				return errors.New("--name is required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"name":             name,
				"description":      description,
				"is_public":        isPublic,
				"memory_enabled":   memoryEnabled,
				"default_provider": firstNonEmpty(defaultProvider, rt.cfg.Defaults.Provider),
				"default_model":    firstNonEmpty(defaultModel, rt.cfg.Defaults.Model),
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/workspaces", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Workspace created")
			output.KV("id", resp["id"])
			output.KV("name", resp["name"])
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Workspace name")
	cmd.Flags().StringVar(&description, "description", "", "Description")
	cmd.Flags().BoolVar(&isPublic, "public", false, "Public workspace")
	cmd.Flags().BoolVar(&memoryEnabled, "memory-enabled", true, "Enable memory")
	cmd.Flags().StringVar(&defaultProvider, "default-provider", "", "Default provider")
	cmd.Flags().StringVar(&defaultModel, "default-model", "", "Default model")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesListCmd() *cobra.Command {
	var includeShared bool
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List workspaces",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := fmt.Sprintf("/workspaces?include_shared=%t", includeShared)
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), path, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, w := range resp {
				rows = append(rows, []string{toString(w["id"]), truncate(toString(w["name"]), 24), toString(w["member_count"]), toString(w["conversation_count"]), toString(w["status"])})
			}
			output.PrintRows([]string{"ID", "Name", "Members", "Conversations", "Status"}, rows)
			return nil
		},
	}
	cmd.Flags().BoolVar(&includeShared, "include-shared", true, "Include shared workspaces")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesGetCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "get <workspace_id>",
		Short: "Get workspace",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/workspaces/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Workspace")
			for _, k := range []string{"id", "name", "description", "owner_id", "status", "member_count", "conversation_count", "share_token"} {
				output.KV(k, resp[k])
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesUpdateCmd() *cobra.Command {
	var name string
	var description string
	var isPublic string
	var memoryEnabled string
	var defaultProvider string
	var defaultModel string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update <workspace_id>",
		Short: "Update workspace",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{}
			if name != "" {
				payload["name"] = name
			}
			if description != "" {
				payload["description"] = description
			}
			if isPublic != "" {
				b, err := strconvBool(isPublic)
				if err != nil {
					return fmt.Errorf("invalid --public value: %w", err)
				}
				payload["is_public"] = b
			}
			if memoryEnabled != "" {
				b, err := strconvBool(memoryEnabled)
				if err != nil {
					return fmt.Errorf("invalid --memory-enabled value: %w", err)
				}
				payload["memory_enabled"] = b
			}
			if defaultProvider != "" {
				payload["default_provider"] = defaultProvider
			}
			if defaultModel != "" {
				payload["default_model"] = defaultModel
			}
			if len(payload) == 0 {
				return errors.New("no update fields provided")
			}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/workspaces/"+url.PathEscape(args[0]), payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Workspace updated")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Workspace name")
	cmd.Flags().StringVar(&description, "description", "", "Description")
	cmd.Flags().StringVar(&isPublic, "public", "", "true|false")
	cmd.Flags().StringVar(&memoryEnabled, "memory-enabled", "", "true|false")
	cmd.Flags().StringVar(&defaultProvider, "default-provider", "", "Default provider")
	cmd.Flags().StringVar(&defaultModel, "default-model", "", "Default model")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <workspace_id>",
		Short: "Delete workspace",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Delete(context.Background(), "/workspaces/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Workspace deleted"))
			return nil
		},
	}
	return cmd
}

func newWorkspacesJoinCmd() *cobra.Command {
	var token string
	cmd := &cobra.Command{
		Use:   "join <workspace_id>",
		Short: "Join workspace by token",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if token == "" {
				return errors.New("--token is required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := "/workspaces/" + url.PathEscape(args[0]) + "/join?share_token=" + url.QueryEscape(token)
			var resp map[string]any
			if err := rt.client.Post(context.Background(), path, map[string]any{}, &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Joined workspace"))
			return nil
		},
	}
	cmd.Flags().StringVar(&token, "token", "", "Share token")
	return cmd
}

func newWorkspacesMembersCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "members <workspace_id>",
		Short: "List workspace members",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/workspaces/"+url.PathEscape(args[0])+"/members", &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, m := range resp {
				rows = append(rows, []string{toString(m["user_id"]), toString(m["email"]), toString(m["role"]), toString(m["can_write"])})
			}
			output.PrintRows([]string{"User ID", "Email", "Role", "Can Write"}, rows)
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesRegenerateTokenCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "regenerate-token <workspace_id>",
		Short: "Regenerate workspace share token",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/workspaces/"+url.PathEscape(args[0])+"/regenerate-token", map[string]any{}, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Share token regenerated")
			output.KV("share_token", resp["share_token"])
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newWorkspacesUseCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "use <workspace_id>",
		Short: "Set default workspace",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			rt.cfg.Defaults.WorkspaceID = args[0]
			if err := saveRuntime(rt); err != nil {
				return err
			}
			output.Success("Default workspace set")
			output.KV("workspace_id", args[0])
			return nil
		},
	}
	return cmd
}

func newWorkspacesCurrentCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "current",
		Short: "Show default workspace",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if rt.cfg.Defaults.WorkspaceID == "" {
				output.Info("No default workspace set")
				return nil
			}
			output.KV("workspace_id", rt.cfg.Defaults.WorkspaceID)
			return nil
		},
	}
}
