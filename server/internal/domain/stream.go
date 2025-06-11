package domain

import "time"

type StartStreamPayload struct {
	StreamType string     `json:"stream_type"`
	StartTime  *time.Time `json:"start_time"`
	EndTime    *time.Time `json:"end_time"`
}

type StopStreamPayload struct {
	StreamType string `json:"stream_type"`
}

type Stream struct {
	StreamType string     `json:"stream_type"`
	Status     string     `json:"status"`
	StartedAt  *time.Time `json:"started_at"`
	FinishedAt *time.Time `json:"finished_at"`
}
