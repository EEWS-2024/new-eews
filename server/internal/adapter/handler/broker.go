package handler

import (
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"os"
	"os/signal"
	handler "server/internal/adapter/handler/station"
	"syscall"
)

type Consumer struct {
	c *kafka.Consumer
	p *kafka.Producer
}

func NewConsumer(brokers, groupID string, topics []string) (err error) {
	cfg := &kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          groupID,
		"auto.offset.reset": "latest",
	}
	c, err := kafka.NewConsumer(cfg)
	if err != nil {
		return err
	}

	if err = c.SubscribeTopics(topics, nil); err != nil {
		return err
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

loop:
	for {
		select {
		case <-sigs:
			fmt.Println("Shutdown signal received")
			break loop
		default:
			event := c.Poll(100)
			if event == nil {
				continue
			}

			switch e := event.(type) {
			case *kafka.Message:
				go handler.PushToClients(e.Value)

			case kafka.Error:
				if e.Code() != kafka.ErrUnknownTopicOrPart {
					return fmt.Errorf("kafka error: %w", e)
				} else {
					fmt.Println("Unknown topic or part", topics)
				}

			default:
				continue
			}
		}
	}

	return nil
}
