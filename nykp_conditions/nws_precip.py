import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd
import pendulum
import pytz
import urllib

DEFAULT_STATION = 'KNYC'
DEFAULT_TIMEZONE = 'America/New_York'
DATETIME_FMT = '%Y-%m-%dT%H:%M:%SZ'
CACHE_DIR = 'cache'


def _get_observations_url(station: str, start_dt: datetime, end_dt: datetime) -> str:
    start = start_dt.astimezone(pytz.UTC).strftime(DATETIME_FMT)
    end = end_dt.astimezone(pytz.UTC).strftime(DATETIME_FMT)
    return 'https://api.weather.gov/stations/{station}/observations?start={start}&end={end}'


def _get_ts_precip(observation: dict) -> Tuple[str, float]:
    ts = observation['timestamp']
    precip_mm = observation['precipitationLastHour']['value']
    return (ts, precip_mm)


def _get_hourly_precips(precip_series: pd.Series) -> pd.Series:
    pass


def _get_6_hour_precips(precip_series: pd.Series) -> pd.Series:
    pass
    


def get_observed_precip(
        station: str = DEFAULT_STATION,
        as_of: Optional[datetime] = None,
        hours: int = 24,
        tz: Union[str, timezone] = DEFAULT_TIMEZONE,
        clean_up=True,
) -> float:
    if isinstance(tz, str):
        tz = pytz.timezone(tz)

    if as_of is None:
        as_of = datetime.now(tz=pytz.timezone(tz))
    elif isinstance(as_of, str):
        as_of = pendulum.parse(as_of)

    start_dt = as_of - timedelta(hours=hours)
    filename_dt_fmt = '%Y%m%dT%H%M%S'
    tmp_filename = f'{station}_observations_{start_dt.strftime(filename_dt_fmt)}_{as_of.strftime(filename_dt_fmt)}.json'
    
    tmp_dir = CACHE_DIR
    tmp_path = os.path.join(tmp_dir, tmp_filename)
    clean_up_paths = []
    if clean_up:
        clean_up_paths.append(tmp_filename)
    
    if not os.path.exists(tmp_dir):
        os.makedirs(os.path.dirname(tmp_path))
        if clean_up:
            clean_up_paths.append(tmp_dir)
    
    url = _get_observations_url(station, start_dt, as_of)
    resp = urllib.request.urlretrieve(url, tmp_path)
    with open(tmp_path) as f:
        retrieved_json = json.load(tmp_path)

    for path in clean_up_paths:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
    
    observations = [feature['properties'] for feature in retrieved_json['features']]
    t, precip_mm = zip(*map(_get_ts_precip, observations))
    precip_mm_series = pd.Series(data=precip_mm, index=pd.to_datetime(t)).sort_index()


def post_observed_precip(channel: str):
    pass
