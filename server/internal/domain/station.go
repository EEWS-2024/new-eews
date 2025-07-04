package domain

type Station struct {
	Code            string   `json:"code"`
	Name            string   `json:"name"`
	Latitude        float64  `json:"latitude"`
	Longitude       float64  `json:"longitude"`
	Elevation       float64  `json:"elevation"`
	NearestStations []string `json:"nearest_stations"`
	IsEnabled       bool     `json:"is_enabled"`
}

type TogglePayload struct {
	StationCode string `json:"code"`
	IsEnabled   bool   `json:"is_enabled"`
}
