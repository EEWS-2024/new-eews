package main

import (
	"fmt"
	"os"
	"picker-go/module"
)

func main() {
	cfg, poller, err := module.Initialize()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Initialization error: %v\n", err)
		os.Exit(1)
	}

	topics := []string{cfg.KafkaTopic}

	if err := poller.Run(topics); err != nil {
		fmt.Fprintf(os.Stderr, "Runtime error: %v\n", err)
		os.Exit(1)
	}
}
