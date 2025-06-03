package accessor

import "picker-go/internal/poller/accessor"

type EpicWaveFormAccessor interface {
	Create(waveForm *accessor.EpicWaveForm) (err error)
}
