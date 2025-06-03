from datetime import datetime
from typing import Dict, List


class DataPollHandler:
    def __init__(self):
        self.data_poll: Dict[str, Dict[str, Dict[str, List[int]]]] = {}

    def poll_data(
        self,
        station: str,
        channel: str,
        start_time: datetime,
        data_points: List[int],
    ):
        formatted_start_time = start_time.strftime("%Y-%m-%dT%H:%M")
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")

        if station not in self.data_poll:
            self.data_poll[station] = {
                formatted_start_time: {
                    channel: data_points,
                }
            }

        if formatted_start_time not in self.data_poll[station]:
            self.data_poll[station][formatted_start_time] = {
                channel: data_points,
            }

        if channel not in self.data_poll[station][formatted_start_time]:
            self.data_poll[station][formatted_start_time][channel] = data_points

        if len(self.data_poll[station][formatted_start_time][channel]) < 600:
            stored_data_points_length = len(self.data_poll[station][formatted_start_time][channel])
            data_points_length = len(data_points)
            exceeded_data_points = 600 - (data_points_length + stored_data_points_length)
            data_points = data_points[:exceeded_data_points]
            self.data_poll[station][formatted_start_time][channel].extend(data_points)

        if len(self.data_poll[station][formatted_start_time][channel]) >= 600:
            data_to_send = self.data_poll[station][formatted_start_time][channel][:600]
            del self.data_poll[station][formatted_start_time]
            return data_to_send, datetime.strptime(formatted_start_time, "%Y-%m-%dT%H:%M")

        return self.__handle_missing_data(
            channel,
            self.data_poll[station][formatted_start_time],
            datetime.strptime(formatted_start_time, "%Y-%m-%dT%H:%M"),
            datetime.strptime(now, "%Y-%m-%dT%H:%M")
        )

    def __handle_missing_data(
        self,
        channel: str,
        polled_data: Dict[str, List[int]],
        start_time: datetime,
        now: datetime,
    ):

        delta = now - start_time
        delta_minutes = delta.total_seconds() / 60

        if delta_minutes >= 1:
            missing_samples = 600 - len(polled_data[channel])

            if missing_samples > 0:
                missing_data = [0] * missing_samples
                polled_data[channel].extend(missing_data)

            data_to_send = polled_data[channel][:600]
            del polled_data
            return data_to_send, start_time