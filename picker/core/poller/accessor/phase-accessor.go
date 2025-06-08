package accessor

import "picker/internal/poller/accessor"

type PhaseAccessor interface {
	Create(waveForm *accessor.EpicWaveForm) (err error)
}
