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

func newChatCmd() *cobra.Command {
	chat := &cobra.Command{Use: "chat", Short: "Chat endpoints"}
	chat.AddCommand(newChatSendCmd())
	chat.AddCommand(newChatConversationsCmd())
	chat.AddCommand(newChatConversationGetCmd())
	chat.AddCommand(newChatConversationDeleteCmd())
	chat.AddCommand(newChatStreamCmd())
	return chat
}

func newChatSendCmd() *cobra.Command {
	var conversationID string
	var workspaceID string
	var layer string
	var includeGlobal bool
	var provider string
	var model string
	var agentsEnabled bool
	var jsonOut bool

	cmd := &cobra.Command{
		Use:   "send [message]",
		Short: "Send chat message",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			mappedLayer := mapChatLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			if mappedLayer == "workspace" && ws == "" {
				return errors.New("workspace_id required for workspace layer")
			}

			payload := map[string]any{
				"content":         strings.Join(args, " "),
				"conversation_id": strings.TrimSpace(conversationID),
				"workspace_id":    ws,
				"layer":           mappedLayer,
				"include_global":  includeGlobal,
				"provider":        firstNonEmpty(provider, rt.cfg.Defaults.Provider),
				"model":           firstNonEmpty(model, rt.cfg.Defaults.Model),
				"agents_enabled":  agentsEnabled,
			}

			if payload["conversation_id"] == "" {
				delete(payload, "conversation_id")
			}
			if payload["workspace_id"] == "" {
				delete(payload, "workspace_id")
			}

			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/chat/message", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			fmt.Println(toString(resp["content"]))
			output.KV("conversation_id", resp["conversation_id"])
			output.KV("provider", resp["provider_used"])
			output.KV("model", resp["model_used"])
			output.KV("confidence", resp["confidence"])
			return nil
		},
	}
	cmd.Flags().StringVar(&conversationID, "conversation-id", "", "Conversation UUID")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace|global")
	cmd.Flags().BoolVar(&includeGlobal, "global", false, "Include global memory")
	cmd.Flags().StringVar(&provider, "provider", "", "Provider")
	cmd.Flags().StringVar(&model, "model", "", "Model")
	cmd.Flags().BoolVar(&agentsEnabled, "agents-enabled", true, "Enable agents")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newChatConversationsCmd() *cobra.Command {
	var workspaceID string
	var limit int
	var offset int
	var jsonOut bool

	cmd := &cobra.Command{
		Use:   "conversations",
		Short: "List chat conversations",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			q := url.Values{}
			q.Set("limit", fmt.Sprintf("%d", limit))
			q.Set("offset", fmt.Sprintf("%d", offset))
			if ws != "" {
				q.Set("workspace_id", ws)
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/chat/conversations?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, c := range resp {
				rows = append(rows, []string{toString(c["id"]), truncate(toString(c["title"]), 30), toString(c["message_count"]), truncate(toString(c["last_message"]), 50)})
			}
			output.PrintRows([]string{"ID", "Title", "Messages", "Last Message"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().IntVar(&limit, "limit", 50, "Limit")
	cmd.Flags().IntVar(&offset, "offset", 0, "Offset")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newChatConversationGetCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "conversation <conversation_id>",
		Short: "Get chat conversation by id",
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
			if err := rt.client.Get(context.Background(), "/chat/conversations/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Conversation")
			output.KV("id", resp["id"])
			output.KV("title", resp["title"])
			output.KV("message_count", resp["message_count"])
			if messages, ok := resp["messages"].([]any); ok {
				for idx, m := range messages {
					item, _ := m.(map[string]any)
					fmt.Printf("\n[%d] %s: %s\n", idx+1, toString(item["role"]), toString(item["content"]))
				}
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newChatConversationDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <conversation_id>",
		Short: "Delete chat conversation",
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
			if err := rt.client.Delete(context.Background(), "/chat/conversations/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Conversation deleted"))
			return nil
		},
	}
	return cmd
}

func newChatStreamCmd() *cobra.Command {
	var workspaceID string
	var layer string
	var includeGlobal bool
	var provider string
	var model string
	var agentsEnabled bool
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "stream [message]",
		Short: "Invoke streaming endpoint (returns raw payload)",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			mappedLayer := mapChatLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			if mappedLayer == "workspace" && ws == "" {
				return errors.New("workspace_id required for workspace layer")
			}
			payload := map[string]any{
				"content":        strings.Join(args, " "),
				"workspace_id":   ws,
				"layer":          mappedLayer,
				"include_global": includeGlobal,
				"provider":       firstNonEmpty(provider, rt.cfg.Defaults.Provider),
				"model":          firstNonEmpty(model, rt.cfg.Defaults.Model),
				"agents_enabled": agentsEnabled,
			}
			if payload["workspace_id"] == "" {
				delete(payload, "workspace_id")
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/chat/stream", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			return output.JSON(resp)
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace|global")
	cmd.Flags().BoolVar(&includeGlobal, "global", false, "Include global memory")
	cmd.Flags().StringVar(&provider, "provider", "", "Provider")
	cmd.Flags().StringVar(&model, "model", "", "Model")
	cmd.Flags().BoolVar(&agentsEnabled, "agents-enabled", true, "Enable agents")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}
