package adapter

import (
	"encoding/json"
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"picker/core/poller/port"
)

type Consumer struct {
	c *kafka.Consumer
	p *kafka.Producer
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
	p, err := kafka.NewProducer(cfg)
	if err != nil {
		return nil, err
	}
	return &Consumer{c: c, p: p}, nil
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

func (kc *Consumer) Publish(topic string, key string, value interface{}) (err error) {
	var msgValue []byte
	if msgValue, err = json.Marshal(value); err != nil {
		return nil
	}

	msg := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topic,
			Partition: kafka.PartitionAny,
		},
		Key:   []byte(key),
		Value: msgValue,
	}

	if err = kc.p.Produce(msg, nil); err != nil {
		return err
	}

	e := <-kc.p.Events()
	switch ev := e.(type) {
	case *kafka.Message:
		if ev.TopicPartition.Error != nil {
			return fmt.Errorf("delivery failed: %w", ev.TopicPartition.Error)
		}
		fmt.Printf("Delivered message to %v\n", ev.TopicPartition)
	default:
	}
	return nil
}

func (kc *Consumer) Close() error {
	return kc.c.Close()
}
