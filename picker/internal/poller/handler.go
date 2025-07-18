package poller

import (
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"math"
	"os"
	"os/signal"
	"picker/core/poller"
	"picker/core/poller/port"
	"picker/internal/config"
	"picker/internal/poller/accessor"
	"strings"
	"syscall"
	"time"
)

type Poller struct {
	Consumer      port.BrokerConsumer
	PollerService *poller.Service
	PolledData    PolledData
	WaveTime      WaveTime
	config        *config.Config
}

func NewPoller(
	consumer port.BrokerConsumer,
	cfg *config.Config,
	db *pgxpool.Pool,
) *Poller {
	ps := poller.NewService(cfg, db)
	pd := PolledData{
		Traces: make(map[string]map[string][]int),
	}
	wt := WaveTime{
		PreviousPTime: make(map[string]time.Time),
		PreviousSTime: make(map[string]time.Time),
	}
	return &Poller{
		Consumer:      consumer,
		PollerService: ps,
		PolledData:    pd,
		WaveTime:      wt,
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

func (r *Poller) Transpose(data [][]int) [600][3]int {
	var transposed [600][3]int
	for i := 0; i < 3; i++ {
		for j := 0; j < 600; j++ {
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

	var timeSeries []map[string]any
	if timeSeries, err = r.GenerateTimeSeries(traceData); err != nil {
		fmt.Fprintf(os.Stderr, "GenerateTimeSeries error: %v\n", err)
		return err
	}

	if err = r.Consumer.Publish(
		r.config.KafkaProducerTopic,
		traceData.Station,
		poller.PublishSpec{
			Type:    "trace",
			Station: traceData.Station,
			Payload: map[string]any{
				"channel": traceData.Channel,
				"data":    timeSeries,
			},
		},
	); err != nil {
		return err
	}

	if polledData := r.Poll(traceData); polledData != nil {
		transposed := r.Transpose(polledData)

		var predictionResult *poller.PredictionResult
		if predictionResult, err = r.PollerService.Predict(
			traceData.Station,
			traceData.StartTime,
			transposed,
			traceData.ModelType,
		); err != nil {
			return err
		}

		previousPTimeExist := false
		previousSTimeExist := false
		var primaryTime time.Time
		var secondaryTime time.Time

		if predictionResult != nil {
			_, previousPTimeExist = r.WaveTime.PreviousPTime[predictionResult.StationCode]
			_, previousSTimeExist = r.WaveTime.PreviousSTime[predictionResult.StationCode]

			primaryTime, err = time.Parse("2006-01-02 15:04:05", predictionResult.PArrTime)
			if err != nil {
				return err
			}

			secondaryTime, err = time.Parse("2006-01-02 15:04:05", predictionResult.SArrTime)
			if err != nil {
				return err
			}

			if predictionResult.PArr || predictionResult.SArr {
				if err = r.Consumer.Publish(
					r.config.KafkaProducerTopic,
					traceData.Station,
					poller.PublishSpec{
						Type:    "phase_picking",
						Station: predictionResult.StationCode,
						Payload: map[string]any{
							"channel":        traceData.Channel,
							"is_p_arrived":   predictionResult.PArr,
							"p_arrival_time": float64(primaryTime.UnixNano() / int64(time.Millisecond)),
							"is_s_arrived":   predictionResult.SArr,
							"s_arrival_time": float64(secondaryTime.UnixNano() / int64(time.Millisecond)),
						},
					},
				); err != nil {
					return err
				}
			}

			if err = r.PollerService.SavePhase(accessor.Phase{
				PickTime:     time.Now(),
				StationCode:  predictionResult.StationCode,
				IsPArrived:   predictionResult.PArr,
				PIndex:       predictionResult.PArrIndex,
				PArrivalTime: primaryTime,
				IsSArrived:   predictionResult.SArr,
				SIndex:       predictionResult.SArrIndex,
				SArrivalTime: secondaryTime,
			}); err != nil {
				return err
			}
		}

		var newWaveForm *poller.PredictionStatsResult
		if predictionResult != nil && predictionResult.PArr && predictionResult.SArr {
			if newWaveForm, err = r.PollerService.PredictStats(
				traceData.Station,
				transposed,
			); err != nil {
				return err
			}
		}

		if predictionResult != nil && previousPTimeExist && !previousSTimeExist {
			var stationTime time.Time
			stationTime, err = time.Parse("2006-01-02 15:04:05", traceData.StartTime)
			if err != nil {
				return err
			}

			diff := stationTime.Sub(r.WaveTime.PreviousPTime[predictionResult.StationCode]).Seconds()

			if (diff >= 60 && !predictionResult.SArr) || predictionResult.SArr {
				if newWaveForm, err = r.PollerService.PredictStats(
					traceData.Station,
					transposed,
				); err != nil {
					return err
				}
			}
		}

		if predictionResult != nil && !previousPTimeExist && predictionResult.PArr {
			r.WaveTime.PreviousPTime[predictionResult.StationCode] = primaryTime
		}

		if predictionResult != nil && !previousSTimeExist && predictionResult.SArr {
			r.WaveTime.PreviousSTime[predictionResult.StationCode] = secondaryTime
		}

		if newWaveForm != nil {
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
				stationCodes := strings.Join(epicWaveForm.StationCodes, ", ")
				//if epicWaveForm.Magnitude > 4.0 {
				if err = r.Consumer.Publish(
					r.config.KafkaProducerTopic,
					stationCodes,
					poller.PublishSpec{
						Type:    "epic_waveform",
						Station: stationCodes,
						Payload: epicWaveForm,
					},
				); err != nil {
					return err
				}
				//}

				if err = r.PollerService.SaveWaveForm(epicWaveForm, waveFormTimeStamps); err != nil {
					return err
				}
			}
		}

	}

	return nil
}

func (r *Poller) GenerateTimeSeries(trace Trace) (timeSeries []map[string]any, err error) {
	timeSeries = make([]map[string]any, 0)

	var startTime time.Time
	if startTime, err = time.Parse("2006-01-02 15:04:05", trace.StartTime); err != nil {
		return nil, err
	}

	var endTime time.Time
	if endTime, err = time.Parse("2006-01-02 15:04:05", trace.EndTime); err != nil {
		return nil, err
	}

	start := float64(startTime.UnixNano() / int64(time.Millisecond))
	end := float64(endTime.UnixNano() / int64(time.Millisecond))

	tick := math.Round(end-start) / float64(len(trace.Data))

	for i, data := range trace.Data {
		timeSeries = append(timeSeries, map[string]any{
			"value": data,
			"time":  start + float64(i)*tick,
		})
	}

	return timeSeries, nil
}
