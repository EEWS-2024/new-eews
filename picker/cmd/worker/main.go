package main

import (
	"log"
	"picker/module"
)

func main() {
	cfg, poller, err := module.Initialize()
	if err != nil {
		log.Fatalf("Initialization error: %v\n", err)
	}

	topics := []string{cfg.KafkaConsumerTopic}

	if err := poller.Run(topics); err != nil {
		log.Fatalf("Runtime error: %v\n", err)
	}
}
