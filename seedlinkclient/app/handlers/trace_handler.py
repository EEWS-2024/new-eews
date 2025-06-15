from threading import Thread
from typing import List

from flask import current_app

from app.handlers.data_poll_handler import DataPollHandler
from app.providers.seedlink_provider import SeedlinkProvider


class TraceHandler:
    def __init__(self):
        self.seedlink_provider = SeedlinkProvider()

    def run(self, stations: List[str], model_type: str):
        self.seedlink_provider.clear_stream()
        context = current_app._get_current_object()

        thread = Thread(
            target=self.seedlink_provider.stream_data,
            args=(
                stations,
                model_type,
                context,
                DataPollHandler,
            )
        )
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
