package main

import (
	"os"

	"neurograph/cli/internal/commands"
)

func main() {
	if err := commands.NewRootCmd().Execute(); err != nil {
		os.Exit(1)
	}
}
