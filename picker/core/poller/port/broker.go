package port

import "picker/core/poller"

type Message struct {
	Topic     string
	Partition int32
	Offset    int64
	Key       []byte
	Value     []byte
}

type BrokerConsumer interface {
	Subscribe(topics []string) error
	Poll(timeout int) (*Message, error)
	Publish(topic string, key string, value poller.PublishSpec) (err error)
	Close() error
}
