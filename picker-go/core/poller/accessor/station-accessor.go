package accessor

import "picker-go/internal/poller/accessor"

type StationAccessor interface {
	GetByStationCode(code string) (station *accessor.Station, err error)
	GetByStationCodes(codes []string) (station []accessor.Station, err error)
}
