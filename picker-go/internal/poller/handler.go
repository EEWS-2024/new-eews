package poller

import (
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"os/signal"
	"picker-go/core/poller"
	"picker-go/core/poller/port"
	"picker-go/internal/config"
	"picker-go/internal/poller/adapter"
	"strings"
	"syscall"
	"time"
)

type Poller struct {
	Consumer      port.BrokerConsumer
	PollerService *poller.Service
	PolledData    PolledData
	config        *config.Config
}

func NewPoller(
	consumer port.BrokerConsumer,
	cfg *config.Config,
	redisClient *adapter.RedisAdapter,
	db *pgxpool.Pool,
) *Poller {
	ps := poller.NewService(cfg, redisClient, db)
	pd := PolledData{
		Traces: make(map[string]map[string][]int),
	}
	return &Poller{
		Consumer:      consumer,
		PollerService: ps,
		PolledData:    pd,
		config:        cfg,
	}
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

			if err = r.ProcessMessage(msg); err != nil {
				fmt.Printf("Error processing message: %v\n", err)
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

func (r *Poller) Poll(trace Trace) (x [][]int) {
	if r.PolledData.Traces[trace.Station] == nil {
		r.PolledData.Traces[trace.Station] = map[string][]int{
			trace.Channel: trace.Data,
		}
	}

	if r.PolledData.Traces[trace.Station][trace.Channel] == nil {
		r.PolledData.Traces[trace.Station][trace.Channel] = trace.Data
	}

	if len(r.PolledData.Traces[trace.Station]) == 3 {
		for _, v := range r.PolledData.Traces[trace.Station] {
			x = append(x, v)
		}

		return x
	}

	return nil
}

func (r *Poller) Transpose(data [][]int) [382][3]int {
	var transposed [382][3]int
	for i := 0; i < 3; i++ {
		for j := 0; j < 382; j++ {
			transposed[j][i] = data[i][j]
		}
	}
	return transposed
}

func (r *Poller) ProcessMessage(message *port.Message) (err error) {
	var traceData Trace

	if err = json.Unmarshal(message.Value, &traceData); err != nil {
		fmt.Fprintf(os.Stderr, "Unmarshal error: %v\n", err)
		return err
	}

	if polledData := r.Poll(traceData); polledData != nil {
		transposed := r.Transpose(polledData)

		var predictionResult *poller.PredictionResult
		if predictionResult, err = r.PollerService.Predict(
			traceData.Station,
			traceData.StartTime,
			transposed,
		); err != nil {
			return err
		}

		if predictionResult != nil && predictionResult.PArr && predictionResult.SArr {
			var newWaveForm *poller.PredictionStatsResult
			if newWaveForm, err = r.PollerService.PredictStats(
				traceData.Station,
				transposed,
			); err != nil {
				return err
			}

			var waveForms []poller.WaveFormSpec
			var waveFormTimeStamps []time.Time
			if waveForms, waveFormTimeStamps, err = r.PollerService.PollWaveform(newWaveForm); err != nil {
				return err
			}

			if waveForms != nil && len(waveForms) >= 3 {
				var epicWaveForm *poller.WaveFormRecalculationResult
				if epicWaveForm, err = r.PollerService.Recalculate(waveForms); err != nil {
					return err
				}
				if err = r.Consumer.Publish(
					r.config.KafkaProducerTopic,
					strings.Join(epicWaveForm.StationCodes, ", "),
					epicWaveForm,
				); err != nil {
					return err
				}

				if err = r.PollerService.Save(epicWaveForm, waveFormTimeStamps); err != nil {
					return err
				}
			}
		}
	}

	return nil
}
