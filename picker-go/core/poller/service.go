package poller

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"io"
	"log"
	"net/http"
	"picker-go/internal/config"
	"picker-go/internal/poller/accessor"
	"picker-go/internal/poller/adapter"
	"time"
)

type Service struct {
	cfg                  *config.Config
	dataPoints           map[string]PredictionSpec
	rc                   *adapter.RedisAdapter
	stationAccessor      *accessor.StationAccessor
	waveFormAccessor     *accessor.WaveFormAccessor
	epicWaveFormAccessor *accessor.EpicWaveFormAccessor
}

func NewService(
	cfg *config.Config,
	redisClient *adapter.RedisAdapter,
	db *pgxpool.Pool,
) *Service {
	sa := accessor.NewStationAccessor(db)
	wfa := accessor.NewWaveFormAccessor(db)
	ewfa := accessor.NewEpicWaveFormAccessor(db)

	return &Service{
		cfg:                  cfg,
		dataPoints:           make(map[string]PredictionSpec),
		rc:                   redisClient,
		stationAccessor:      sa,
		waveFormAccessor:     wfa,
		epicWaveFormAccessor: ewfa,
	}
}

func (s *Service) Predict(
	stationCode string,
	startTime string,
	data [600][3]int,
) (result *PredictionResult, err error) {
	payload := map[string]interface{}{
		"station_code": stationCode,
		"start_time":   startTime,
		"x":            data,
		"model_type":   "phasenet",
	}

	serialized, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(
		fmt.Sprintf("%s/predict", s.cfg.MachineLearningBaseUrl),
		"application/json",
		bytes.NewReader(serialized),
	)
	if err != nil {
		log.Printf("POST failed: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal(body, &result)
	if err != nil {
		log.Printf("Response marshalling failed: %v", err)
		return nil, err
	}

	// save the result after syahrul predict the index of P/S
	return result, nil
}

func (s *Service) PredictStats(
	stationCode string,
	data [600][3]int,
) (result *PredictionStatsResult, err error) {
	payload := map[string]interface{}{
		"station_code": stationCode,
		"x":            data,
	}

	serialized, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(
		fmt.Sprintf("%s/predict/stats", s.cfg.MachineLearningBaseUrl),
		"application/json",
		bytes.NewReader(serialized),
	)
	if err != nil {
		log.Printf("POST failed: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal(body, &result)
	if err != nil {
		log.Printf("Response marshalling failed: %v", err)
		return nil, err
	}

	return result, nil
}

func (s *Service) Recalculate(waveForms []WaveFormSpec) (result *WaveFormRecalculationResult, err error) {
	stationCodes := make([]string, 0)
	latitudes := make([]float64, 0)
	longitudes := make([]float64, 0)
	magnitudes := make([]float64, 0)
	distances := make([]float64, 0)

	for _, w := range waveForms {
		stationCodes = append(stationCodes, w.StationCode)
		latitudes = append(latitudes, w.Latitude)
		longitudes = append(longitudes, w.Longitude)
		magnitudes = append(magnitudes, w.Magnitude)
		distances = append(distances, w.Distance)
	}

	payload := map[string]interface{}{
		"station_codes": stationCodes,
		"latitudes":     latitudes,
		"longitudes":    longitudes,
		"magnitudes":    magnitudes,
		"distances":     distances,
	}

	serialized, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(
		fmt.Sprintf("%s/predict/recalculate", s.cfg.MachineLearningBaseUrl),
		"application/json",
		bytes.NewReader(serialized),
	)
	if err != nil {
		log.Printf("POST failed: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal(body, &result)
	if err != nil {
		fmt.Print(string(body))
		log.Printf("Response marshalling failed: %v", err)
		return nil, err
	}

	return result, nil
}

func (s *Service) PollWaveform(newWaveForm *PredictionStatsResult) (completedWaveForms []WaveFormSpec, waveFormTimeStamps []time.Time, err error) {
	completedWaveForms = make([]WaveFormSpec, 0)

	var station *accessor.Station
	if station, err = s.stationAccessor.GetByStationCode(newWaveForm.StationCode); err != nil {
		return nil, nil, err
	}

	if station == nil {
		return nil, nil, nil
	}

	if err = s.waveFormAccessor.Create(&accessor.WaveForm{
		PickTime:    time.Now(),
		StationCode: newWaveForm.StationCode,
		Depth:       newWaveForm.Depth,
		Distance:    newWaveForm.Distance,
		Magnitude:   newWaveForm.Magnitude,
	}); err != nil {
		return nil, nil, err
	}

	var stations []*accessor.Station
	if stations, err = s.stationAccessor.GetByStationCodes(station.NearestStations); err != nil {
		return completedWaveForms, nil, err
	}

	stations = append(stations, station)

	for _, st := range stations {
		if len(st.NearestStations) < 2 {
			continue
		}
		nearestStationCodes := st.NearestStations
		nearestStationCodes = append(nearestStationCodes, st.Code)
		waveFormTimeStamps = make([]time.Time, 0)
		for _, stationCode := range nearestStationCodes {
			var wf *accessor.WaveForm
			if wf, err = s.waveFormAccessor.GetLatestByStationCode(stationCode); err != nil {
				return nil, nil, err
			}
			if wf == nil {
				continue
			}
			var nst *accessor.Station
			if nst, err = s.stationAccessor.GetByStationCode(stationCode); err != nil {
				return nil, nil, err
			}
			completedWaveForms = append(completedWaveForms, WaveFormSpec{
				StationCode: wf.StationCode,
				Magnitude:   wf.Magnitude,
				Distance:    wf.Distance,
				Latitude:    nst.Latitude,
				Longitude:   nst.Longitude,
			})
			waveFormTimeStamps = append(waveFormTimeStamps, wf.PickTime)
			if len(completedWaveForms) >= 3 {
				return completedWaveForms, waveFormTimeStamps, nil
			}
		}
		completedWaveForms = completedWaveForms[:0]
	}

	return nil, nil, nil
}

func (s *Service) Save(waveForm *WaveFormRecalculationResult, waveFormTimeStamps []time.Time) (err error) {
	if err = s.epicWaveFormAccessor.Create(&accessor.EpicWaveForm{
		EventTime:    time.Now(),
		StationCodes: waveForm.StationCodes,
		Latitude:     waveForm.Latitude,
		Longitude:    waveForm.Longitude,
		Magnitude:    waveForm.Magnitude,
	}); err != nil {
		return err
	}

	if err = s.waveFormAccessor.Deactivate(waveFormTimeStamps); err != nil {
		return err
	}

	return nil
}
