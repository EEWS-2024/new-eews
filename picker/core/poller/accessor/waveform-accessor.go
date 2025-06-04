package accessor

import (
	"picker/internal/poller/accessor"
)

type WaveFormAccessor interface {
	GetLatestByStationCode(stationCode string) (waveForm *accessor.WaveForm, err error)
	Create(waveForm *accessor.WaveForm) (err error)
}
