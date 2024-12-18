import time

from obspy import Trace


def trace_mapper(trace: Trace):
    return {
        "type": "trace",
        "network": trace.stats.network,
        "station": trace.stats.station,
        "channel": trace.stats.channel,
        "location": trace.stats.location,
        "start_time": str(trace.stats.starttime),
        "end_time": str(trace.stats.endtime),
        "delta": trace.stats.delta,
        "npts": trace.stats.npts,
        "calib": trace.stats.calib,
        "data": trace.data.tolist(),
        "len": len(trace.data.tolist()),
        "sampling_rate": trace.stats.sampling_rate,
        "published_at": time.time(),
    }