package commands

import (
	"context"
	"errors"
	"fmt"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newProfileCmd() *cobra.Command {
	profile := &cobra.Command{Use: "profile", Short: "Profile routes"}
	profile.AddCommand(newProfileSettingsCmd())
	profile.AddCommand(newProfileUpdateUserCmd())
	profile.AddCommand(newProfileUpdatePasswordCmd())
	profile.AddCommand(newProfileUpdateSettingsCmd())
	profile.AddCommand(newProfileExportCmd())
	return profile
}

func newProfileSettingsCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "settings",
		Short: "Get profile settings",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/profile/settings", &resp); err != nil {
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

func newProfileUpdateUserCmd() *cobra.Command {
	var fullName string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update-user",
		Short: "Update profile user",
		RunE: func(cmd *cobra.Command, args []string) error {
			if fullName == "" {
				return errors.New("--full-name is required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{"full_name": fullName}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/profile/user", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Profile updated")
			output.KV("email", resp["email"])
			return nil
		},
	}
	cmd.Flags().StringVar(&fullName, "full-name", "", "Full name")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newProfileUpdatePasswordCmd() *cobra.Command {
	var currentPassword string
	var newPassword string
	var confirmPassword string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update-password",
		Short: "Update password",
		RunE: func(cmd *cobra.Command, args []string) error {
			if currentPassword == "" || newPassword == "" || confirmPassword == "" {
				return errors.New("--current-password --new-password --confirm-password are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"current_password": currentPassword,
				"new_password":     newPassword,
				"confirm_password": confirmPassword,
			}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/profile/password", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Password updated"))
			return nil
		},
	}
	cmd.Flags().StringVar(&currentPassword, "current-password", "", "Current password")
	cmd.Flags().StringVar(&newPassword, "new-password", "", "New password")
	cmd.Flags().StringVar(&confirmPassword, "confirm-password", "", "Confirm password")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newProfileUpdateSettingsCmd() *cobra.Command {
	var defaultProvider string
	var defaultModel string
	var defaultMemoryLayer string
	var agentsEnabled string
	var theme string
	var compactMode string
	var showConfidence string
	var showReasoning string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update-settings",
		Short: "Update profile settings",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			payload := map[string]any{}
			if defaultProvider != "" {
				payload["default_provider"] = defaultProvider
			}
			if defaultModel != "" {
				payload["default_model"] = defaultModel
			}
			if defaultMemoryLayer != "" {
				payload["default_memory_layer"] = defaultMemoryLayer
			}
			if agentsEnabled != "" {
				b, err := strconvBool(agentsEnabled)
				if err != nil {
					return fmt.Errorf("invalid --agents-enabled value: %w", err)
				}
				payload["agents_enabled"] = b
			}
			if theme != "" {
				payload["theme"] = theme
			}
			if compactMode != "" {
				b, err := strconvBool(compactMode)
				if err != nil {
					return fmt.Errorf("invalid --compact-mode value: %w", err)
				}
				payload["compact_mode"] = b
			}
			if showConfidence != "" {
				b, err := strconvBool(showConfidence)
				if err != nil {
					return fmt.Errorf("invalid --show-confidence value: %w", err)
				}
				payload["show_confidence"] = b
			}
			if showReasoning != "" {
				b, err := strconvBool(showReasoning)
				if err != nil {
					return fmt.Errorf("invalid --show-reasoning value: %w", err)
				}
				payload["show_reasoning"] = b
			}
			if len(payload) == 0 {
				return errors.New("no update fields provided")
			}

			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/profile/settings", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Settings updated"))
			return nil
		},
	}
	cmd.Flags().StringVar(&defaultProvider, "default-provider", "", "Default provider")
	cmd.Flags().StringVar(&defaultModel, "default-model", "", "Default model")
	cmd.Flags().StringVar(&defaultMemoryLayer, "default-memory-layer", "", "personal|workspace|global")
	cmd.Flags().StringVar(&agentsEnabled, "agents-enabled", "", "true|false")
	cmd.Flags().StringVar(&theme, "theme", "", "dark|light|system")
	cmd.Flags().StringVar(&compactMode, "compact-mode", "", "true|false")
	cmd.Flags().StringVar(&showConfidence, "show-confidence", "", "true|false")
	cmd.Flags().StringVar(&showReasoning, "show-reasoning", "", "true|false")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newProfileExportCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "export",
		Short: "Export profile data",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/profile/export", &resp); err != nil {
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
