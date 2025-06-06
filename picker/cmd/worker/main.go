package main

import (
	"log"
	"picker/module"
)

func main() {
	_, poller, err := module.Initialize()
	if err != nil {
		log.Fatalf("Initialization error: %v\n", err)
	}

	if err := poller.Run(); err != nil {
		log.Fatalf("Runtime error: %v\n", err)
	}
}
