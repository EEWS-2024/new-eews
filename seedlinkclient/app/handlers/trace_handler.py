from threading import Thread
from typing import List

from app.providers.seedlink_provider import SeedlinkProvider


class TraceHandler:
    def __init__(self):
        self.seedlink_provider = SeedlinkProvider()

    def run(self, stations: List[str]):
        self.seedlink_provider.clear_stream()

        thread = Thread(target=self.seedlink_provider.stream_data, args=(stations,))
        thread.daemon = True  # Dies if main process dies
        thread.start()

        return {
            "status": "success",
        }

    def stop(self):
        self.seedlink_provider.stop_stream()
        return {
            "status": "success",
        }
