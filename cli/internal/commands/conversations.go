package commands

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"strings"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newConversationsCmd() *cobra.Command {
	conv := &cobra.Command{Use: "conversations", Short: "Conversation routes"}
	conv.AddCommand(newConversationsCreateCmd())
	conv.AddCommand(newConversationsListCmd())
	conv.AddCommand(newConversationsGetCmd())
	conv.AddCommand(newConversationsUpdateCmd())
	conv.AddCommand(newConversationsDeleteCmd())
	conv.AddCommand(newConversationsStepsCmd())
	return conv
}

func newConversationsCreateCmd() *cobra.Command {
	var workspaceID string
	var title string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create conversation",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{}
			if ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID); ws != "" {
				payload["workspace_id"] = ws
			}
			if title != "" {
				payload["title"] = title
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/conversations", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Conversation created")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().StringVar(&title, "title", "", "Title")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newConversationsListCmd() *cobra.Command {
	var workspaceID string
	var includeArchived bool
	var limit int
	var offset int
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List conversations",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			if ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID); ws != "" {
				q.Set("workspace_id", ws)
			}
			q.Set("include_archived", fmt.Sprintf("%t", includeArchived))
			q.Set("limit", fmt.Sprintf("%d", limit))
			q.Set("offset", fmt.Sprintf("%d", offset))

			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/conversations?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, c := range resp {
				rows = append(rows, []string{toString(c["id"]), truncate(toString(c["title"]), 30), toString(c["message_count"]), toString(c["is_archived"])})
			}
			output.PrintRows([]string{"ID", "Title", "Messages", "Archived"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().BoolVar(&includeArchived, "include-archived", false, "Include archived")
	cmd.Flags().IntVar(&limit, "limit", 50, "Limit")
	cmd.Flags().IntVar(&offset, "offset", 0, "Offset")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newConversationsGetCmd() *cobra.Command {
	var includeMessages bool
	var messageLimit int
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "get <conversation_id>",
		Short: "Get conversation",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			q.Set("include_messages", fmt.Sprintf("%t", includeMessages))
			q.Set("message_limit", fmt.Sprintf("%d", messageLimit))
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/conversations/"+url.PathEscape(args[0])+"?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Conversation")
			output.KV("id", resp["id"])
			output.KV("title", resp["title"])
			output.KV("message_count", resp["message_count"])
			if msgs, ok := resp["messages"].([]any); ok {
				for i, m := range msgs {
					item, _ := m.(map[string]any)
					fmt.Printf("\n[%d] %s: %s\n", i+1, toString(item["role"]), toString(item["content"]))
				}
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&includeMessages, "include-messages", true, "Include messages")
	cmd.Flags().IntVar(&messageLimit, "message-limit", 100, "Message limit")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newConversationsUpdateCmd() *cobra.Command {
	var title string
	var pinned string
	var archived string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "update <conversation_id>",
		Short: "Update conversation",
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
			if title != "" {
				payload["title"] = title
			}
			if pinned != "" {
				b, err := strconvBool(pinned)
				if err != nil {
					return fmt.Errorf("invalid --pinned value: %w", err)
				}
				payload["is_pinned"] = b
			}
			if archived != "" {
				b, err := strconvBool(archived)
				if err != nil {
					return fmt.Errorf("invalid --archived value: %w", err)
				}
				payload["is_archived"] = b
			}
			if len(payload) == 0 {
				return errors.New("no update fields provided")
			}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/conversations/"+url.PathEscape(args[0]), payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Conversation updated")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "Title")
	cmd.Flags().StringVar(&pinned, "pinned", "", "Set pinned true|false")
	cmd.Flags().StringVar(&archived, "archived", "", "Set archived true|false")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newConversationsDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <conversation_id>",
		Short: "Delete conversation",
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
			if err := rt.client.Delete(context.Background(), "/conversations/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Conversation deleted"))
			return nil
		},
	}
	return cmd
}

func newConversationsStepsCmd() *cobra.Command {
	var messageID string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "steps <conversation_id>",
		Short: "Get processing steps",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := "/conversations/" + url.PathEscape(args[0]) + "/steps"
			if messageID != "" {
				path += "?message_id=" + url.QueryEscape(messageID)
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), path, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, s := range resp {
				rows = append(rows, []string{toString(s["step_number"]), toString(s["action"]), toString(s["status"]), truncate(toString(s["result"]), 60)})
			}
			output.PrintRows([]string{"Step", "Action", "Status", "Result"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&messageID, "message-id", "", "Filter by message UUID")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func strconvBool(v string) (bool, error) {
	switch strings.ToLower(strings.TrimSpace(v)) {
	case "true", "1", "yes", "y", "on":
		return true, nil
	case "false", "0", "no", "n", "off":
		return false, nil
	default:
		return false, errors.New("expected true or false")
	}
}
