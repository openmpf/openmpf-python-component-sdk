#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2024 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2024 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################

from __future__ import annotations

import contextlib
import functools
import inspect
import json
import logging
import time
import typing
from typing import (Callable, Dict, Iterable, Iterator, Optional, Protocol,
                    TypedDict, TypeVar, Union)

T = TypeVar('T')

JsonValue = Union[float, int, str, bool, None]

MetricFunc = Callable[[float], JsonValue]

Metrics = Dict[str, MetricFunc]

class TimingDict(TypedDict):
    name: str
    seconds: float
    metrics: Dict[str, JsonValue]


class Timing:
    def __init__(self, reporter: TimingReporter):
        self._reporter = reporter

    @classmethod
    def with_logger(cls, logger: logging.Logger, level: int = logging.INFO):
        return cls(LoggerReporter(logger, level) )


    @contextlib.contextmanager
    def timer_ctx(self, timer_name: str, metrics: Optional[Metrics] = None, started: bool = True):
        timer = Timer(timer_name, self._reporter)
        if metrics:
            timer.add_metrics(metrics)
        if started:
            timer.start()
        try:
            yield timer
        finally:
            timer.pause()
            timer.report_timing()


    @typing.overload
    def time_func(
            self,
            name_or_func: Callable[..., T],
            metrics: Optional[Metrics] = None) -> Callable[..., T]:
        ...

    @typing.overload
    def time_func(
            self,
            name_or_func: str,
            metrics: Optional[Metrics] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
        ...

    def time_func(
            self,
            name_or_func: Union[str, Callable[..., T]],
            metrics: Optional[Metrics] = None):
        if callable(name_or_func):
            # Handle the case where decorator was applied directly to a function.
            func = name_or_func
            return typing.cast(
                Callable[..., T],
                self._wrap_func(func, func.__name__, metrics))
        else:
            # Handle the case where parameters were passed to the decorator.
            name = name_or_func
            return lambda func: self._wrap_func(func, name, metrics)

    def _wrap_func(
            self,
            func: Callable[..., T],
            timer_name: str,
            metrics: Optional[Metrics]):
        if inspect.isgeneratorfunction(func):
            @functools.wraps(func)
            def generator_wrapper(*args, **kwargs):
                with self.timer_ctx(timer_name, metrics):
                    rv = yield from func(*args, **kwargs)
                    return rv
            return generator_wrapper
        else:
            @functools.wraps(func)
            def func_wrapper(*args, **kwargs):
                with self.timer_ctx(timer_name, metrics):
                    return func(*args, **kwargs)
            return func_wrapper


    def manual_timer(self, timer_name: str) -> Timer:
        return Timer(timer_name, self._reporter)


    def iterator(
            self,
            timer_name: str,
            iterable: Iterable[T],
            metrics: Optional[Metrics] = None) -> Iterator[T]:
        with self.timer_ctx(timer_name, metrics) as timer:
            num_iterations = 0
            for item in iterable:
                num_iterations += 1
                yield item
            timer.add_metric('iterations/sec', lambda sec: num_iterations / sec)


    def detailed_iter(
            self,
            timer_name: str,
            iterable: Iterable[T],
            metrics: Optional[Metrics] = None):
        with self.timer_ctx(timer_name, metrics) as overall_timer:
            loop_body_timer = self.manual_timer(timer_name)
            num_iterations = 0
            for item in iterable:
                num_iterations += 1
                with loop_body_timer.time_segment():
                    yield item

            overall_timer.pause()
            overall_timer.add_metrics({
                'iterations/sec': lambda sec: num_iterations / sec,
                'loop body time (s)': lambda _: loop_body_timer.seconds_elapsed,
                'iterator time (s)': lambda sec: sec - loop_body_timer.seconds_elapsed
            })


class TimingReporter(Protocol):
    def __call__(self, timing_dict: TimingDict):
        ...


class LoggerReporter(TimingReporter):
    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self._logger = logger
        self._level = level

    def __call__(self, timing_dict: TimingDict):
        timing_str = json.dumps(timing_dict)
        self._logger.log(self._level, 'Timing - %s', timing_str)


class PrintReporter(TimingReporter):
    def __call__(self, timing_dict: TimingDict):
        timing_str = json.dumps(timing_dict)
        print(f'Timing - {timing_str}')


class Timer:
    def __init__(self, name: str, reporter: TimingReporter = PrintReporter()):
        self.name = name
        self._seconds_elapsed = 0.0
        self._last_start_time = None
        self._metrics: Metrics = {}
        self._reporter = reporter

    def start(self) -> Timer:
        if self._last_start_time is None:
            self._last_start_time = time.perf_counter()
        return self

    def pause(self) -> float:
        self._seconds_elapsed = self.seconds_elapsed
        self._last_start_time = None
        return self._seconds_elapsed

    @property
    def seconds_elapsed(self) -> float:
        if self._last_start_time is None:
            return self._seconds_elapsed
        time_since_start = time.perf_counter() - self._last_start_time
        return self._seconds_elapsed + time_since_start

    def add_metric(self, metric_name: str, metric_func: MetricFunc) -> Timer:
        self._metrics[metric_name] = metric_func
        return self

    def add_metrics(self, metrics: Metrics) -> Timer:
        self._metrics.update(metrics)
        return self

    def report_timing(self) -> Timer:
        self._reporter(self.get_timing_dict())
        return self

    def get_timing_dict(self) -> TimingDict:
        seconds_elapsed = self.seconds_elapsed
        return {
            'name': self.name,
            'seconds': seconds_elapsed,
            'metrics': {n: f(seconds_elapsed) for n, f in self._metrics.items()}
        }

    @contextlib.contextmanager
    def time_segment(self):
        self.start()
        try:
            yield self
        finally:
            self.pause()
