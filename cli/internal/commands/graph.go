package commands

import (
	"context"
	"fmt"
	"net/url"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newGraphCmd() *cobra.Command {
	graph := &cobra.Command{Use: "graph", Short: "Graph routes"}
	graph.AddCommand(newGraphEntitiesCmd())
	graph.AddCommand(newGraphEntityGetCmd())
	graph.AddCommand(newGraphEntityCreateCmd())
	graph.AddCommand(newGraphEntityDeleteCmd())
	graph.AddCommand(newGraphRelationshipsCmd())
	graph.AddCommand(newGraphRelationshipCreateCmd())
	graph.AddCommand(newGraphRelationshipDeleteCmd())
	graph.AddCommand(newGraphVisualizeCmd())
	graph.AddCommand(newGraphPathsCmd())
	graph.AddCommand(newGraphCentralityCmd())
	return graph
}

func newGraphEntitiesCmd() *cobra.Command {
	var query string
	var typesCSV string
	var layer string
	var limit int
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "entities",
		Short: "List/search entities",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			q.Set("q", query)
			q.Set("limit", fmt.Sprintf("%d", limit))
			if layer != "" {
				q.Set("layer", mapLayer(layer))
			}
			for _, t := range splitCSV(typesCSV) {
				q.Add("types", t)
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/graph/entities?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, e := range resp {
				rows = append(rows, []string{toString(e["id"]), toString(e["name"]), toString(e["type"]), toString(e["layer"])})
			}
			output.PrintRows([]string{"ID", "Name", "Type", "Layer"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&query, "query", "", "Query")
	cmd.Flags().StringVar(&typesCSV, "types", "", "Comma-separated types")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer")
	cmd.Flags().IntVar(&limit, "limit", 50, "Limit")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphEntityGetCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "entity <entity_id>",
		Short: "Get entity",
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
			if err := rt.client.Get(context.Background(), "/graph/entities/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Heading("Entity")
			for _, k := range []string{"id", "name", "type", "layer"} {
				output.KV(k, resp[k])
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphEntityCreateCmd() *cobra.Command {
	var name string
	var entityType string
	var layer string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "create-entity",
		Short: "Create entity",
		RunE: func(cmd *cobra.Command, args []string) error {
			if name == "" || entityType == "" {
				return fmt.Errorf("--name and --type are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{"name": name, "entity_type": entityType, "layer": mapLayer(firstNonEmpty(layer, rt.cfg.Defaults.Layer))}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/graph/entities", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Entity created")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Entity name")
	cmd.Flags().StringVar(&entityType, "type", "", "Entity type")
	cmd.Flags().StringVar(&layer, "layer", "", "Layer")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphEntityDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete-entity <entity_id>",
		Short: "Delete entity",
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
			if err := rt.client.Delete(context.Background(), "/graph/entities/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Entity deleted"))
			return nil
		},
	}
	return cmd
}

func newGraphRelationshipsCmd() *cobra.Command {
	var direction string
	var typesCSV string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "relationships <entity_id>",
		Short: "List entity relationships",
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
			q.Set("direction", firstNonEmpty(direction, "both"))
			for _, t := range splitCSV(typesCSV) {
				q.Add("types", t)
			}
			var resp []map[string]any
			if err := rt.client.Get(context.Background(), "/graph/relationships/"+url.PathEscape(args[0])+"?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for _, r := range resp {
				rows = append(rows, []string{toString(r["id"]), toString(r["source_id"]), toString(r["type"]), toString(r["target_id"]), toString(r["confidence"])})
			}
			output.PrintRows([]string{"ID", "Source", "Type", "Target", "Confidence"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&direction, "direction", "both", "incoming|outgoing|both")
	cmd.Flags().StringVar(&typesCSV, "types", "", "Comma-separated relationship types")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphRelationshipCreateCmd() *cobra.Command {
	var sourceID string
	var targetID string
	var relationshipType string
	var reason string
	var confidence float64
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "create-relationship",
		Short: "Create relationship",
		RunE: func(cmd *cobra.Command, args []string) error {
			if sourceID == "" || targetID == "" || relationshipType == "" {
				return fmt.Errorf("--source-id, --target-id, and --type are required")
			}
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			payload := map[string]any{
				"source_id":         sourceID,
				"target_id":         targetID,
				"relationship_type": relationshipType,
				"reason":            reason,
				"confidence":        confidence,
			}
			var resp map[string]any
			if err := rt.client.Post(context.Background(), "/graph/relationships", payload, &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			output.Success("Relationship created")
			output.KV("id", resp["id"])
			return nil
		},
	}
	cmd.Flags().StringVar(&sourceID, "source-id", "", "Source entity ID")
	cmd.Flags().StringVar(&targetID, "target-id", "", "Target entity ID")
	cmd.Flags().StringVar(&relationshipType, "type", "", "Relationship type")
	cmd.Flags().StringVar(&reason, "reason", "", "Reason")
	cmd.Flags().Float64Var(&confidence, "confidence", 1.0, "Confidence 0..1")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphRelationshipDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete-relationship <relationship_id>",
		Short: "Delete relationship",
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
			if err := rt.client.Delete(context.Background(), "/graph/relationships/"+url.PathEscape(args[0]), &resp); err != nil {
				return err
			}
			output.Success(firstNonEmpty(toString(resp["message"]), "Relationship deleted"))
			return nil
		},
	}
	return cmd
}

func newGraphVisualizeCmd() *cobra.Command {
	var centerEntity string
	var depth int
	var maxNodes int
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "visualize",
		Short: "Get graph visualization subset",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			q.Set("depth", fmt.Sprintf("%d", depth))
			q.Set("max_nodes", fmt.Sprintf("%d", maxNodes))
			if centerEntity != "" {
				q.Set("center_entity", centerEntity)
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/graph/visualize?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			nodes, _ := resp["nodes"].([]any)
			edges, _ := resp["edges"].([]any)
			output.KV("nodes", len(nodes))
			output.KV("edges", len(edges))
			return nil
		},
	}
	cmd.Flags().StringVar(&centerEntity, "center-entity", "", "Center entity id")
	cmd.Flags().IntVar(&depth, "depth", 2, "Depth")
	cmd.Flags().IntVar(&maxNodes, "max-nodes", 100, "Max nodes")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphPathsCmd() *cobra.Command {
	var maxDepth int
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "paths <source_id> <target_id>",
		Short: "Find graph paths",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := "/graph/paths/" + url.PathEscape(args[0]) + "/" + url.PathEscape(args[1]) + "?max_depth=" + url.QueryEscape(fmt.Sprintf("%d", maxDepth))
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
	cmd.Flags().IntVar(&maxDepth, "max-depth", 5, "Max path depth")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newGraphCentralityCmd() *cobra.Command {
	var entityIDsCSV string
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "centrality",
		Short: "Get centrality",
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			q := url.Values{}
			for _, id := range splitCSV(entityIDsCSV) {
				q.Add("entity_ids", id)
			}
			var resp map[string]any
			if err := rt.client.Get(context.Background(), "/graph/centrality?"+q.Encode(), &resp); err != nil {
				return err
			}
			if jsonOut {
				return output.JSON(resp)
			}
			rows := make([][]string, 0, len(resp))
			for id, degree := range resp {
				rows = append(rows, []string{id, toString(degree)})
			}
			output.PrintRows([]string{"Entity", "Degree"}, rows)
			return nil
		},
	}
	cmd.Flags().StringVar(&entityIDsCSV, "entity-ids", "", "Comma-separated entity IDs")
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}
