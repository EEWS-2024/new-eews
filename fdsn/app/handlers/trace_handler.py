from threading import Thread
from typing import List

from flask import current_app

from app.handlers.data_poll_handler import DataPollHandler
from app.providers.fdsn_provider import FdsnProvider


class TraceHandler:
    def __init__(self):
        self.fdsn_client = FdsnProvider()

    def run(
        self,
        stations: List[str],
        start_time: str,
        end_time: str,
        model_type: str
    ):
        self.fdsn_client.clear_stream()
        context = current_app._get_current_object()

        thread = Thread(
            target=self.fdsn_client.stream_data,
            args=(
                stations,
                start_time,
                end_time,
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
        self.fdsn_client.stop_stream()
        return {
            "status": "success",
        }
