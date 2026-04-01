package output

import (
	"encoding/json"
	"fmt"
	"strings"
)

func Heading(title string) {
	fmt.Printf("\n%s\n%s\n", title, strings.Repeat("-", len(title)))
}

func Info(msg string) {
	fmt.Printf("[i] %s\n", msg)
}

func Success(msg string) {
	fmt.Printf("[+] %s\n", msg)
}

func Warn(msg string) {
	fmt.Printf("[!] %s\n", msg)
}

func Error(msg string) {
	fmt.Printf("[x] %s\n", msg)
}

func KV(key string, value any) {
	fmt.Printf("%-20s %v\n", key+":", value)
}

func JSON(v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	fmt.Println(string(b))
	return nil
}

func PrintRows(headers []string, rows [][]string) {
	if len(headers) == 0 {
		return
	}

	widths := make([]int, len(headers))
	for i, h := range headers {
		widths[i] = len(h)
	}
	for _, row := range rows {
		for i, c := range row {
			if i < len(widths) && len(c) > widths[i] {
				widths[i] = len(c)
			}
		}
	}

	for i, h := range headers {
		fmt.Printf("%-*s", widths[i]+2, h)
	}
	fmt.Println()
	for _, w := range widths {
		fmt.Print(strings.Repeat("-", w), "  ")
	}
	fmt.Println()
	for _, row := range rows {
		for i, c := range row {
			if i < len(widths) {
				fmt.Printf("%-*s", widths[i]+2, c)
			}
		}
		fmt.Println()
	}
}
