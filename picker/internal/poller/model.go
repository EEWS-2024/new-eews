package poller

import "time"

type Trace struct {
	Network      string  `json:"network"`
	Station      string  `json:"station"`
	Channel      string  `json:"channel"`
	Location     string  `json:"location"`
	StartTime    string  `json:"start_time"`
	EndTime      string  `json:"end_time"`
	Delta        float64 `json:"delta"`
	Npts         int     `json:"npts"`
	Calib        float64 `json:"calib"`
	SamplingRate float64 `json:"sampling_rate"`
	ArrivalTime  float64 `json:"arrival_time"`
	Type         string  `json:"type"`
	Data         []int   `json:"data"`
	ModelType    string  `json:"model_type"`
}

type PolledData struct {
	Traces map[string]map[string][]int `json:"traces"`
}

type WaveTime struct {
	PreviousPTime map[string]time.Time `json:"previous_p_time"`
	PreviousSTime map[string]time.Time `json:"previous_s_time"`
}
