package commands

import (
	"context"
	"errors"
	"fmt"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newAuthCmd() *cobra.Command {
	auth := &cobra.Command{Use: "auth", Short: "Authentication commands"}
	auth.AddCommand(newAuthRegisterCmd())
	auth.AddCommand(newAuthLoginCmd())
	auth.AddCommand(newAuthRefreshCmd())
	auth.AddCommand(newAuthLogoutCmd())
	auth.AddCommand(newAuthMeCmd())
	return auth
}

func newAuthRegisterCmd() *cobra.Command {
	var email string
	var password string
	var fullName string

	cmd := &cobra.Command{
		Use:   "register",
		Short: "Register user",
		RunE: func(cmd *cobra.Command, args []string) error {
			if email == "" || password == "" {
				return errors.New("email and password are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			payload := map[string]any{"email": email, "password": password, "full_name": fullName}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/auth/register", payload, &resp); err != nil {
				return err
			}
			output.Success("Registered successfully")
			output.KV("Email", toString(resp["email"]))
			return nil
		},
	}
	cmd.Flags().StringVar(&email, "email", "", "Email")
	cmd.Flags().StringVar(&password, "password", "", "Password")
	cmd.Flags().StringVar(&fullName, "full-name", "", "Full name")
	_ = cmd.MarkFlagRequired("email")
	_ = cmd.MarkFlagRequired("password")
	return cmd
}

func newAuthLoginCmd() *cobra.Command {
	var email string
	var password string

	cmd := &cobra.Command{
		Use:   "login",
		Short: "Login and store tokens",
		RunE: func(cmd *cobra.Command, args []string) error {
			if email == "" || password == "" {
				return errors.New("email and password are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			resp, err := rt.client.Login(context.Background(), email, password)
			if err != nil {
				return err
			}

			access := toString(resp["access_token"])
			refresh := toString(resp["refresh_token"])
			expires := toInt64(resp["expires_in"])
			if access == "" || refresh == "" {
				return fmt.Errorf("invalid token response")
			}
			rt.cfg.SetTokens(access, refresh, expires)
			if err := saveRuntime(rt); err != nil {
				return err
			}
			output.Success("Logged in")

			var me map[string]any
			if err := rt.client.Get(context.Background(), "/auth/me", &me); err == nil {
				output.KV("User", toString(me["email"]))
			}
			return nil
		},
	}

	cmd.Flags().StringVar(&email, "email", "", "Email")
	cmd.Flags().StringVar(&password, "password", "", "Password")
	_ = cmd.MarkFlagRequired("email")
	_ = cmd.MarkFlagRequired("password")
	return cmd
}

func newAuthRefreshCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "refresh",
		Short: "Refresh access token",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if rt.cfg.Auth.RefreshToken == "" {
				return errors.New("no refresh token; login first")
			}
			resp, err := rt.client.Refresh(context.Background())
			if err != nil {
				return err
			}
			rt.cfg.SetTokens(toString(resp["access_token"]), toString(resp["refresh_token"]), toInt64(resp["expires_in"]))
			if err := saveRuntime(rt); err != nil {
				return err
			}
			output.Success("Token refreshed")
			return nil
		},
	}
}

func newAuthLogoutCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "logout",
		Short: "Logout and clear local tokens",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if rt.cfg.Auth.AccessToken != "" {
				_ = rt.client.Post(context.Background(), "/auth/logout", nil, nil)
			}
			rt.cfg.ClearTokens()
			if err := saveRuntime(rt); err != nil {
				return err
			}
			output.Success("Logged out")
			return nil
		},
	}
}

func newAuthMeCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "me",
		Short: "Show current user",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/auth/me", &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Current User")
			output.KV("ID", toString(resp["id"]))
			output.KV("Email", toString(resp["email"]))
			output.KV("Full Name", toString(resp["full_name"]))
			output.KV("Active", toBool(resp["is_active"]))
			output.KV("Created", toString(resp["created_at"]))
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}
