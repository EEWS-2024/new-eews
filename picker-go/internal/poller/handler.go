package poller

import (
	"fmt"
	"os"
	"os/signal"
	"picker-go/core/poller/port"
	"syscall"
	"time"
)

type Poller struct {
	Consumer port.BrokerConsumer
}

func NewPoller(consumer port.BrokerConsumer) *Poller {
	return &Poller{Consumer: consumer}
}

func (r *Poller) Run(topics []string) error {
	if err := r.Consumer.Subscribe(topics); err != nil {
		return fmt.Errorf("subscribe failed: %w", err)
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Consumer started; awaiting messages...")
loop:
	for {
		select {
		case <-sigs:
			fmt.Println("Shutdown signal received")
			break loop
		default:
			msg, err := r.Consumer.Poll(100)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Poll error: %v\n", err)
				time.Sleep(1 * time.Second)
				continue
			}
			if msg == nil {
				continue
			}
			// --- Business logic goes here ---
			fmt.Printf("Received: topic=%s partition=%d offset=%d key=%s value=%s\n",
				msg.Topic, msg.Partition, msg.Offset, string(msg.Key), string(msg.Value))
		}
	}

	fmt.Println("Closing consumer")
	return r.Consumer.Close()
}
