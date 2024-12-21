from typing import Set

import numpy as np

from picker.src import pipeline_function


class PipelineService:
    def __init__(self, station: str, pipeline_model_path: str):
        self._states: dict = {}
        self._names: Set[str] = set()
        self.pipeline_model_path = pipeline_model_path

        self._name = station

        self.pipelines = []

        self.init_duration = 382
        self.init_state = {
            "init": [],
            "init_len": 0
        }

        self._processing_function = self._init

    def set_name(self, name: str) -> str:
        i = 0
        while True:
            new_name = f"{self._name}_{name}_{i}"
            if new_name not in self._names:
                self._names.add(new_name)
                break
            i += 1
        return new_name

    def reset(self):
        pass

    def _build_pipeline(self, init_x: np.ndarray):
        with open(self.pipeline_model_path) as f:
            x = init_x
            for line in f:
                pipeline: pipeline_function.Pipeline = eval(
                    "pipeline_function." + line
                )
                pipeline.set_parent(self)
                pipeline.set_initial_state(x)
                x = pipeline.compute(x)
                self.pipelines.append(pipeline)

        return x

    def _process(self, x: np.array):
        for pipeline in self.pipelines:
            x = pipeline.compute(x)
        return x

    def process(self, x: np.ndarray) -> np.ndarray:  # Generator state machine
        return self._processing_function(x)

    def _init(self, x: np.ndarray) -> np.ndarray:
        # Get the latest warmup x
        init = self.init_state["init"]
        init_len = self.init_state["init_len"]

        # Update state
        init.append(x)
        init_len += len(x)

        # Save state
        self.init_state["init"] = init
        self.init_state["init_len"] = init_len

        # Case if not enough data to perform inference
        if init_len < self.init_duration:
            raise PipelineHasNotBeenInitializedException

        # When there are enough data, end initialization state
        x = np.concatenate(init, axis=0)
        x = self._build_pipeline(x)
        self._processing_function = self._process

        return x


class PipelineHasNotBeenInitializedException(Exception):
    pass