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

func newMemoryCmd() *cobra.Command {
	memory := &cobra.Command{Use: "memory", Short: "Memory commands"}
	memory.AddCommand(newMemoryRememberCmd())
	memory.AddCommand(newMemoryRecallCmd())
	memory.AddCommand(newMemorySearchCmd())
	memory.AddCommand(newMemoryListCmd())
	memory.AddCommand(newMemoryCountCmd())
	memory.AddCommand(newMemoryStatusCmd())
	memory.AddCommand(newMemoryGetCmd())
	memory.AddCommand(newMemoryDeleteCmd())
	memory.AddCommand(newMemoryLockCmd())
	memory.AddCommand(newMemoryPositionCmd())
	memory.AddCommand(newMemoryDuplicateCmd())
	memory.AddCommand(newMemoryDetailCmd())
	memory.AddCommand(newMemoryEdgesCmd())
	return memory
}

func newMemoryRememberCmd() *cobra.Command {
	var layer string
	var workspaceID string

	cmd := &cobra.Command{
		Use:   "remember [content]",
		Short: "Store memory",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			mapped := mapLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)

			payload := map[string]any{
				"content": strings.Join(args, " "),
				"layer":   mapped,
			}
			if mapped == "tenant" {
				if ws == "" {
					return errors.New("workspace_id required for workspace layer")
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
			output.KV("Layer", toString(resp["layer"]))
			return nil
		},
	}
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace|global")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	return cmd
}

func newMemoryRecallCmd() *cobra.Command {
	var layersCSV string
	var workspaceID string
	var limit int
	var minConfidence float64
	var jsonOut bool

	cmd := &cobra.Command{
		Use:   "recall [query]",
		Short: "Recall memories",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			layers := splitCSV(firstNonEmpty(layersCSV, rt.cfg.Defaults.Layer))
			for i := range layers {
				layers[i] = mapLayer(layers[i])
			}
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)

			payload := map[string]any{
				"query":          strings.Join(args, " "),
				"layers":         layers,
				"max_results":    limit,
				"min_confidence": minConfidence,
			}
			if contains(layers, "tenant") {
				if ws == "" {
					return errors.New("workspace_id required when layers include workspace")
				}
				payload["workspace_id"] = ws
			}

			var resp []map[string]any
			if err := rt.client.Post(context.Background(), "/memory/recall", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			if len(resp) == 0 {
				output.Info("No results")
				return nil
			}
			for i, m := range resp {
				output.Heading(fmt.Sprintf("Result %d", i+1))
				output.KV("ID", toString(m["id"]))
				output.KV("Layer", toString(m["layer"]))
				output.KV("Score", toString(m["score"]))
				fmt.Println(toString(m["content"]))
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&layersCSV, "layers", "", "Comma-separated layers")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().IntVar(&limit, "limit", 10, "Max results")
	cmd.Flags().Float64Var(&minConfidence, "min-confidence", 0.5, "Minimum confidence")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemorySearchCmd() *cobra.Command {
	var layersCSV string
	var workspaceID string
	var limit int
	var jsonOut bool

	cmd := &cobra.Command{
		Use:   "search [query]",
		Short: "Search memory",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			layers := splitCSV(firstNonEmpty(layersCSV, rt.cfg.Defaults.Layer))
			for i := range layers {
				layers[i] = mapLayer(layers[i])
			}
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)

			q := url.Values{}
			q.Set("q", strings.Join(args, " "))
			q.Set("limit", fmt.Sprintf("%d", limit))
			for _, l := range layers {
				q.Add("layers", l)
			}
			if ws != "" {
				q.Set("workspace_id", ws)
			}

			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/memory/search?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, m := range resp {
				rows = append(rows, []string{toString(m["id"]), toString(m["layer"]), toString(m["score"]), truncate(toString(m["content"]), 80)})
			}
			output.PrintRows([]string{"ID", "Layer", "Score", "Content"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&layersCSV, "layers", "", "Comma-separated layers")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().IntVar(&limit, "limit", 20, "Max results")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryListCmd() *cobra.Command {
	var layer string
	var workspaceID string
	var limit int
	var offset int
	var jsonOut bool

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List memories",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}

			mapped := mapLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)

			q := url.Values{}
			q.Set("layer", mapped)
			q.Set("limit", fmt.Sprintf("%d", limit))
			q.Set("offset", fmt.Sprintf("%d", offset))
			if mapped == "tenant" {
				if ws == "" {
					return errors.New("workspace_id required for workspace layer")
				}
				q.Set("workspace_id", ws)
			}

			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/memory/list?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, m := range resp {
				rows = append(rows, []string{toString(m["id"]), toString(m["layer"]), toString(m["confidence"]), truncate(toString(m["content"]), 80)})
			}
			output.PrintRows([]string{"ID", "Layer", "Confidence", "Content"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace|global")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().IntVar(&limit, "limit", 50, "Max results")
	cmd.Flags().IntVar(&offset, "offset", 0, "Offset")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryCountCmd() *cobra.Command {
	var workspaceID string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "count",
		Short: "Memory count",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			path := "/memory/count"
			if ws != "" {
				path += "?workspace_id=" + url.QueryEscape(ws)
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), path, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Memory Count")
			for k, v := range resp {
				output.KV(k, v)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryStatusCmd() *cobra.Command {
	var workspaceID string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "status",
		Short: "Memory status",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			path := "/memory/status"
			if ws != "" {
				path += "?workspace_id=" + url.QueryEscape(ws)
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), path, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Memory Status")
			for k, v := range resp {
				output.KV(k, v)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryGetCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "get <id>",
		Short: "Get memory by ID",
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
			if err := rt.client.Get(context.Background(), "/memory/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Memory")
			for _, k := range []string{"id", "layer", "confidence", "created_at", "updated_at"} {
				output.KV(k, resp[k])
			}
			fmt.Println(toString(resp["content"]))
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <id>",
		Short: "Delete memory by ID",
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
			if err := rt.client.Delete(context.Background(), "/memory/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(toString(resp["message"]))
			return nil
		},
	}
	return cmd
}

func newMemoryLockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "lock <id>",
		Short: "Toggle memory lock",
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
			if err := rt.client.Patch(context.Background(), "/memory/"+url.PathEscape(args[0])+"/lock", map[string]any{}, &resp); err != nil {
				return err
			}
			output.Success("Lock toggled")
			output.KV("is_locked", resp["is_locked"])
			return nil
		},
	}
	return cmd
}

func newMemoryPositionCmd() *cobra.Command {
	var x float64
	var y float64
	cmd := &cobra.Command{
		Use:   "position <id>",
		Short: "Update memory position",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{"x": x, "y": y}
			var resp map[string]any
			if err := rt.client.Patch(context.Background(), "/memory/"+url.PathEscape(args[0])+"/position", payload, &resp); err != nil {
				return err
			}
			output.Success("Position updated")
			output.KV("x", resp["x"])
			output.KV("y", resp["y"])
			return nil
		},
	}
	cmd.Flags().Float64Var(&x, "x", 0, "X position")
	cmd.Flags().Float64Var(&y, "y", 0, "Y position")
	_ = cmd.MarkFlagRequired("x")
	_ = cmd.MarkFlagRequired("y")
	return cmd
}

func newMemoryDuplicateCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "duplicate <id>",
		Short: "Duplicate memory",
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
			if err := rt.client.Post(context.Background(), "/memory/"+url.PathEscape(args[0])+"/duplicate", map[string]any{}, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Memory duplicated")
			output.KV("New ID", resp["id"])
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryDetailCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "detail <id>",
		Short: "Get memory detail",
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
			if err := rt.client.Get(context.Background(), "/memory/"+url.PathEscape(args[0])+"/detail", &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Memory Detail")
			for _, k := range []string{"id", "layer", "confidence", "is_locked", "embedding_dim", "created_at"} {
				output.KV(k, resp[k])
			}
			fmt.Println(toString(resp["content"]))
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryEdgesCmd() *cobra.Command {
	edges := &cobra.Command{Use: "edges", Short: "Memory edge commands"}
	edges.AddCommand(newMemoryEdgesCreateCmd())
	edges.AddCommand(newMemoryEdgesListCmd())
	edges.AddCommand(newMemoryEdgesDeleteCmd())
	return edges
}

func newMemoryEdgesCreateCmd() *cobra.Command {
	var reason string
	var confidence float64
	cmd := &cobra.Command{
		Use:   "create <source_id> <target_id>",
		Short: "Create edge between two memories",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"source_id":  args[0],
				"target_id":  args[1],
				"reason":     reason,
				"confidence": confidence,
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/memory/edges", payload, &resp); err != nil {
				return err
			}
			output.Success("Edge created")
			output.KV("ID", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&reason, "reason", "", "Reason")
	cmd.Flags().Float64Var(&confidence, "confidence", 0.8, "Confidence 0..1")
	return cmd
}

func newMemoryEdgesListCmd() *cobra.Command {
	var layer string
	var workspaceID string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List memory edges",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			mapped := mapLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))
			ws := firstNonEmpty(workspaceID, rt.cfg.Defaults.WorkspaceID)
			q := url.Values{}
			q.Set("layer", mapped)
			if mapped == "tenant" {
				if ws == "" {
					return errors.New("workspace_id required for workspace layer")
				}
				q.Set("workspace_id", ws)
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/memory/edges?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, e := range resp {
				rows = append(rows, []string{toString(e["id"]), toString(e["source_id"]), toString(e["target_id"]), toString(e["confidence"]), toString(e["connection_count"])})
			}
			output.PrintRows([]string{"ID", "Source", "Target", "Confidence", "Count"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&layer, "layer", "", "Layer personal|workspace")
	cmd.Flags().StringVar(&workspaceID, "workspace-id", "", "Workspace UUID")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newMemoryEdgesDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <edge_id>",
		Short: "Delete memory edge",
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
			if err := rt.client.Delete(context.Background(), "/memory/edges/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(toString(resp["message"]))
			return nil
		},
	}
	return cmd
}
