from fastapi.params import Depends

from producer.src.providers.obspy.obspy_port import ObspyPort
from producer.src.providers.obspy.seedlink_adapter import SeedLinkAdapter
from producer.src.services.stream_service_interface import StreamServiceInterface


class StreamService(StreamServiceInterface):
    def __init__(self, seedlink_provider: ObspyPort = Depends(SeedLinkAdapter)):
        self.seedlink_provider = seedlink_provider

    def start_trace(self):
        self.seedlink_provider.start_streaming()

    def stop_trace(self):
        self.seedlink_provider.stop_streaming()