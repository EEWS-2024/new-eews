package poller

type WaveFormSpec struct {
	StationCode string  `json:"station_code"`
	Latitude    float64 `json:"latitude"`
	Longitude   float64 `json:"longitude"`
	Magnitude   float64 `json:"magnitude"`
	Distance    float64 `json:"distance"`
}

type WaveFormRecalculationResult struct {
	StationCodes []string `json:"station_codes"`
	Magnitude    float64  `json:"magnitude"`
	Latitude     float64  `json:"latitude"`
	Longitude    float64  `json:"longitude"`
}

type PredictionSpec struct {
	StationCode string
	StartTime   string
	X           [][]int
}

type PredictionResult struct {
	InitEnd     bool   `json:"init_end"`
	NewPEvent   bool   `json:"new_p_event"`
	NewSEvent   bool   `json:"new_s_event"`
	PArr        bool   `json:"p_arr"`
	PArrTime    string `json:"p_arr_time"`
	PArrIndex   int    `json:"p_arr_index"`
	SArr        bool   `json:"s_arr"`
	SArrTime    string `json:"s_arr_time"`
	SArrIndex   int    `json:"s_arr_index"`
	StationCode string `json:"station_code"`
}

type PredictionStatsResult struct {
	Depth       float64 `json:"depth"`
	Distance    float64 `json:"distance"`
	Magnitude   float64 `json:"magnitude"`
	StationCode string  `json:"station_code"`
}

type PublishSpec struct {
	Type    string      `json:"type"`
	Payload interface{} `json:"payload"`
}
