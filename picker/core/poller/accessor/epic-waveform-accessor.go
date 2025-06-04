package accessor

import "picker/internal/poller/accessor"

type EpicWaveFormAccessor interface {
	Create(waveForm *accessor.EpicWaveForm) (err error)
}
