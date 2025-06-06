package poller

import (
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"os"
	"picker/core/poller"
	"picker/core/poller/port"
	"picker/internal/config"
	"strings"
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

func (r *Poller) Run(topics []string) (err error) {
	var file *os.File

	if file, err = os.Open("payloads.json"); err != nil {
		fmt.Println("Error opening file:", err)
		return
	}
	defer file.Close()

	var messages []Trace
	decoder := json.NewDecoder(file)
	if err = decoder.Decode(&messages); err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	for _, msg := range messages {
		fmt.Println("Processing message:", msg.Station)
		if err, _ = r.ProcessMessage(msg); err != nil {
			fmt.Printf("Error processing message: %v\n", err)
			return
		}
		fmt.Println("Processing Done\n")
	}

	return
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

func (r *Poller) ProcessMessage(traceData Trace) (err error, isCompleted bool) {
	if polledData := r.Poll(traceData); polledData != nil {
		transposed := r.Transpose(polledData)

		var predictionResult *poller.PredictionResult
		if predictionResult, err = r.PollerService.Predict(
			traceData.Station,
			traceData.StartTime,
			transposed,
		); err != nil {
			return err, false
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
				return err, false
			}

			secondaryTime, err = time.Parse("2006-01-02 15:04:05", predictionResult.SArrTime)
			if err != nil {
				return err, false
			}
		}

		var newWaveForm *poller.PredictionStatsResult
		if predictionResult != nil && predictionResult.PArr && predictionResult.SArr {
			if newWaveForm, err = r.PollerService.PredictStats(
				traceData.Station,
				transposed,
			); err != nil {
				return err, false
			}
		}

		if predictionResult != nil && previousPTimeExist && !previousSTimeExist {
			var stationTime time.Time
			stationTime, err = time.Parse("2006-01-02 15:04:05", traceData.StartTime)
			if err != nil {
				return err, false
			}

			diff := stationTime.Sub(r.WaveTime.PreviousPTime[predictionResult.StationCode]).Seconds()

			if (diff >= 60 && !predictionResult.SArr) || predictionResult.SArr {
				if newWaveForm, err = r.PollerService.PredictStats(
					traceData.Station,
					transposed,
				); err != nil {
					return err, false
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
				return err, false
			}

			if waveForms != nil && len(waveForms) >= 3 {
				var epicWaveForm *poller.WaveFormRecalculationResult
				if epicWaveForm, err = r.PollerService.Recalculate(waveForms); err != nil {
					return err, false
				}
				if err = r.Consumer.Publish(
					r.config.KafkaProducerTopic,
					strings.Join(epicWaveForm.StationCodes, ", "),
					epicWaveForm,
				); err != nil {
					return err, false
				}

				if err = r.PollerService.Save(epicWaveForm, waveFormTimeStamps); err != nil {
					return err, false
				}

				return nil, true
			}
		}

	}

	return nil, false
}
