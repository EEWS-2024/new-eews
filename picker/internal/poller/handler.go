package poller

import (
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/shirou/gopsutil/v3/process"
	"os"
	"picker/core/poller"
	"picker/internal/config"
	"time"
)

type Poller struct {
	PollerService *poller.Service
	PolledData    PolledData
	WaveTime      WaveTime
	config        *config.Config
}

func NewPoller(
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
		PollerService: ps,
		PolledData:    pd,
		WaveTime:      wt,
		config:        cfg,
	}
}

func (r *Poller) Run() (err error) {
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

	pid := int32(os.Getpid())
	proc, err := process.NewProcess(pid)
	if err != nil {
		panic(err)
	}

	startTime := time.Now()
	nData := 0
	sumSeconds := 0.0
	mlTotalExecutionTime := 0.0
	for _, msg := range messages {
		tStartTime := time.Now()
		fmt.Println("Processing message:", msg.Station)
		mlExecutionTime := 0.0
		if err, mlExecutionTime = r.ProcessMessage(msg); err != nil {
			fmt.Printf("Error processing message: %v\n", err)
			return
		}
		mlTotalExecutionTime += mlExecutionTime
		tExecutionTime := time.Now().Sub(tStartTime).Seconds()
		sumSeconds += tExecutionTime - mlExecutionTime
		nData += len(msg.Data)
		fmt.Println("Processing Done\n")
	}
	endTime := time.Now()

	time.Sleep(500 * time.Millisecond)
	cpuPercent, _ := proc.CPUPercent()
	memPercent, _ := proc.MemoryPercent()

	avgThroughput := float64(nData) / sumSeconds
	fmt.Println("Avg Throughput of Picker Service (n/s):", avgThroughput)

	executionTime := endTime.Sub(startTime).Seconds() - mlTotalExecutionTime
	fmt.Println("Execution Time of Picker Service (s):", executionTime)

	fmt.Println("CPU Usage of Picker Service (%):", cpuPercent)
	fmt.Println("Memory Usage of Picker Service (%):", memPercent)

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

func (r *Poller) ProcessMessage(traceData Trace) (err error, mlExecutionTime float64) {
	if polledData := r.Poll(traceData); polledData != nil {
		transposed := r.Transpose(polledData)

		var predictionResult *poller.PredictionResult
		predictTime := 0.0
		if predictionResult, err, predictTime = r.PollerService.Predict(
			traceData.Station,
			traceData.StartTime,
			transposed,
		); err != nil {
			return err, mlExecutionTime
		}
		mlExecutionTime += predictTime

		previousPTimeExist := false
		previousSTimeExist := false
		var primaryTime time.Time
		var secondaryTime time.Time

		if predictionResult != nil {
			_, previousPTimeExist = r.WaveTime.PreviousPTime[predictionResult.StationCode]
			_, previousSTimeExist = r.WaveTime.PreviousSTime[predictionResult.StationCode]

			primaryTime, err = time.Parse("2006-01-02 15:04:05", predictionResult.PArrTime)
			if err != nil {
				return err, mlExecutionTime
			}

			secondaryTime, err = time.Parse("2006-01-02 15:04:05", predictionResult.SArrTime)
			if err != nil {
				return err, mlExecutionTime
			}
		}

		var newWaveForm *poller.PredictionStatsResult
		predictStatsTime := 0.0
		if predictionResult != nil && predictionResult.PArr && predictionResult.SArr {
			if newWaveForm, err, predictStatsTime = r.PollerService.PredictStats(
				traceData.Station,
				transposed,
			); err != nil {
				return err, mlExecutionTime
			}
		}

		if predictionResult != nil && previousPTimeExist && !previousSTimeExist {
			var stationTime time.Time
			stationTime, err = time.Parse("2006-01-02 15:04:05", traceData.StartTime)
			if err != nil {
				return err, mlExecutionTime
			}

			diff := stationTime.Sub(r.WaveTime.PreviousPTime[predictionResult.StationCode]).Seconds()

			if (diff >= 60 && !predictionResult.SArr) || predictionResult.SArr {
				if newWaveForm, err, predictStatsTime = r.PollerService.PredictStats(
					traceData.Station,
					transposed,
				); err != nil {
					return err, mlExecutionTime
				}
			}
		}

		mlExecutionTime += predictStatsTime

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
				return err, mlExecutionTime
			}

			if waveForms != nil && len(waveForms) >= 3 {
				var epicWaveForm *poller.WaveFormRecalculationResult
				recalculateTime := 0.0
				if epicWaveForm, err, recalculateTime = r.PollerService.Recalculate(waveForms); err != nil {
					return err, mlExecutionTime
				}
				mlExecutionTime += recalculateTime

				if err = r.PollerService.Save(epicWaveForm, waveFormTimeStamps); err != nil {
					return err, mlExecutionTime
				}

				return nil, mlExecutionTime
			}
		}

	}

	return nil, mlExecutionTime
}
