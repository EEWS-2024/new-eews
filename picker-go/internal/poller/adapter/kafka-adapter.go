package adapter

import (
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"picker-go/core/poller/port"
)

type Consumer struct {
	c *kafka.Consumer
}

func NewConsumer(brokers, groupID string) (port.BrokerConsumer, error) {
	cfg := &kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          groupID,
		"auto.offset.reset": "latest",
	}
	c, err := kafka.NewConsumer(cfg)
	if err != nil {
		return nil, err
	}
	return &Consumer{c: c}, nil
}

func (kc *Consumer) Subscribe(topics []string) error {
	return kc.c.SubscribeTopics(topics, nil)
}

func (kc *Consumer) Poll(timeoutMs int) (*port.Message, error) {
	ev := kc.c.Poll(timeoutMs)
	if ev == nil {
		return nil, nil
	}

	switch e := ev.(type) {
	case *kafka.Message:
		return &port.Message{
			Topic:     *e.TopicPartition.Topic,
			Partition: e.TopicPartition.Partition,
			Offset:    int64(e.TopicPartition.Offset),
			Key:       e.Key,
			Value:     e.Value,
		}, nil

	case kafka.Error:
		return nil, fmt.Errorf("kafka error: %w", e)

	default:
		return nil, nil
	}
}

func (kc *Consumer) Close() error {
	return kc.c.Close()
}
