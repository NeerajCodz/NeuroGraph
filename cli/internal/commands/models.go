package commands

import (
	"context"

	"github.com/spf13/cobra"

	"neurograph/cli/internal/output"
)

func newModelsCmd() *cobra.Command {
	models := &cobra.Command{Use: "models", Short: "Model routes"}
	models.AddCommand(newModelsProvidersCmd())
	models.AddCommand(newModelsAllCmd())
	models.AddCommand(newModelsProviderCmd())
	models.AddCommand(newModelsGeminiCmd())
	models.AddCommand(newModelsGroqCmd())
	models.AddCommand(newModelsNvidiaCmd())
	models.AddCommand(newModelsTestCmd())
	models.AddCommand(newModelsRecommendationsCmd())
	return models
}

func newModelsProvidersCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "providers",
		Short: "List providers",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/providers", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsAllCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "all",
		Short: "List all models",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/all", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsProviderCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "provider <provider_id>",
		Short: "List models by provider",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/provider/"+args[0], jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsGeminiCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "gemini",
		Short: "List Gemini models",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/gemini", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsGroqCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "groq",
		Short: "List Groq models",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/groq", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsNvidiaCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "nvidia",
		Short: "List NVIDIA models",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/nvidia", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsTestCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "test <provider_id> <model_id>",
		Short: "Test model",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			rt, err := loadRuntime()
			if err != nil {
				return err
			}
			if err := requireLogin(rt); err != nil {
				return err
			}
			path := "/models/test/" + args[0] + "/" + args[1]
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
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func newModelsRecommendationsCmd() *cobra.Command {
	var jsonOut bool
	cmd := &cobra.Command{
		Use:   "recommendations",
		Short: "Get model recommendations",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runModelGet("/models/recommendations", jsonOut)
		},
	}
	cmd.Flags().BoolVar(&jsonOut, "json", false, "JSON output")
	return cmd
}

func runModelGet(path string, jsonOut bool) error {
	rt, err := loadRuntime()
	if err != nil {
		return err
	}
	if err := requireLogin(rt); err != nil {
		return err
	}
	var resp map[string]any
	if err := rt.client.Get(context.Background(), path, &resp); err != nil {
		return err
	}
	if jsonOut {
		return output.JSON(resp)
	}
	return output.JSON(resp)
}
