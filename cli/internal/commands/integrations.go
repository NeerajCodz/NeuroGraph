package commands

import (
	"context"
	"errors"
	"fmt"
	"net/url"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newIntegrationsCmd() *cobra.Command {
	intg := &cobra.Command{Use: "integrations", Short: "Integration routes"}
	intg.AddCommand(newIntegrationsConnectionsCmd())
	intg.AddCommand(newIntegrationsConnectionGetCmd())
	intg.AddCommand(newIntegrationsConnectionCreateCmd())
	intg.AddCommand(newIntegrationsConnectionUpdateCmd())
	intg.AddCommand(newIntegrationsConnectionDeleteCmd())
	intg.AddCommand(newIntegrationsTypesCmd())
	intg.AddCommand(newIntegrationsOAuthInitiateCmd())
	intg.AddCommand(newIntegrationsOAuthCallbackCmd())
	return intg
}

func newIntegrationsConnectionsCmd() *cobra.Command {
	var tenantID string
	var integrationType string
	var scope string
	var enabledOnly bool
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "connections",
		Short: "List integration connections",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			if tenantID != "" {
				q.Set("tenant_id", tenantID)
			}
			if integrationType != "" {
				q.Set("integration_type", integrationType)
			}
			if scope != "" {
				q.Set("scope", scope)
			}
			if enabledOnly {
				q.Set("enabled_only", "true")
			}
			path := "/integrations/connections"
			if qs := q.Encode(); qs != "" {
				path += "?" + qs
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), path, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&tenantID, "tenant-id", "", "Tenant/Workspace UUID")
	cmd.Flags().StringVar(&integrationType, "integration-type", "", "Integration type")
	cmd.Flags().StringVar(&scope, "scope", "", "Scope personal|workspace")
	cmd.Flags().BoolVar(&enabledOnly, "enabled-only", false, "Only enabled")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newIntegrationsConnectionGetCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "get <connection_id>",
		Short: "Get connection",
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
			if err := rt.client.Get(context.Background(), "/integrations/connections/"+url.PathEscape(args[0]), &resp); err != nil {
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

func newIntegrationsConnectionCreateCmd() *cobra.Command {
	var integrationType string
	var scope string
	var tenantID string
	var name string
	var enabled bool
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create integration connection",
		RunE: func(cmd *cobra.Command, args []string) error {
			if integrationType == "" {
				return errors.New("--integration-type is required")
			}
			if scope == "workspace" && tenantID == "" {
				return errors.New("--tenant-id is required when --scope workspace")
			}
			if scope == "personal" && tenantID != "" {
				return errors.New("--tenant-id is not allowed when --scope personal")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"integration_type": integrationType,
				"scope":            firstNonEmpty(scope, "personal"),
				"name":             name,
				"enabled":          enabled,
				"config":           map[string]any{},
			}
			if tenantID != "" {
				payload["tenant_id"] = tenantID
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/integrations/connections", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Connection created")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&integrationType, "integration-type", "", "Integration type")
	cmd.Flags().StringVar(&scope, "scope", "personal", "Scope")
	cmd.Flags().StringVar(&tenantID, "tenant-id", "", "Tenant/Workspace UUID")
	cmd.Flags().StringVar(&name, "name", "", "Connection name")
	cmd.Flags().BoolVar(&enabled, "enabled", true, "Enabled")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newIntegrationsOAuthCallbackCmd() *cobra.Command {
	var code string
	var state string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "oauth-callback",
		Short: "Complete OAuth callback flow",
		RunE: func(cmd *cobra.Command, args []string) error {
			if code == "" || state == "" {
				return errors.New("--code and --state are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := "/integrations/oauth/callback?code=" + url.QueryEscape(code) + "&state=" + url.QueryEscape(state)
			var resp map[string]any
			if err := rt.client.Post(context.Background(), path, map[string]any{}, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&code, "code", "", "OAuth authorization code")
	cmd.Flags().StringVar(&state, "state", "", "OAuth state")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newIntegrationsConnectionUpdateCmd() *cobra.Command {
	var name string
	var enabled string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update <connection_id>",
		Short: "Update connection",
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
			if enabled != "" {
				b, err := strconvBool(enabled)
				if err != nil {
					return fmt.Errorf("invalid --enabled value: %w", err)
				}
				payload["enabled"] = b
			}
			if len(payload) == 0 {
				return errors.New("no update fields provided")
			}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/integrations/connections/"+url.PathEscape(args[0]), payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Connection updated")
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Connection name")
	cmd.Flags().StringVar(&enabled, "enabled", "", "true|false")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newIntegrationsConnectionDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <connection_id>",
		Short: "Delete connection",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			if err := rt.client.Delete(context.Background(), "/integrations/connections/"+url.PathEscape(args[0]), nil); err != nil {
				return err
			}
			output.Success("Connection deleted")
			return nil
		},
	}
	return cmd
}

func newIntegrationsTypesCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "types",
		Short: "List integration types",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/integrations/types", &resp); err != nil {
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

func newIntegrationsOAuthInitiateCmd() *cobra.Command {
	var integrationType string
	var scope string
	var tenantID string
	var redirectURI string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "oauth-initiate",
		Short: "Initiate OAuth flow",
		RunE: func(cmd *cobra.Command, args []string) error {
			if integrationType == "" || redirectURI == "" {
				return errors.New("--integration-type and --redirect-uri are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"integration_type": integrationType,
				"scope":            firstNonEmpty(scope, "personal"),
				"redirect_uri":     redirectURI,
			}
			if tenantID != "" {
				payload["tenant_id"] = tenantID
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/integrations/oauth/initiate", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&integrationType, "integration-type", "", "Integration type")
	cmd.Flags().StringVar(&scope, "scope", "personal", "Scope")
	cmd.Flags().StringVar(&tenantID, "tenant-id", "", "Tenant/Workspace UUID")
	cmd.Flags().StringVar(&redirectURI, "redirect-uri", "", "OAuth redirect URI")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}
