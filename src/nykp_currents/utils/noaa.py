from collections.abc import Sequence
from dataclasses import dataclass
import os
from typing import Optional
from urllib.request import urlretrieve

import pandas as pd
import pendulum

CSV_URL_BASE = 'https://tidesandcurrents.noaa.gov/noaacurrents/DownloadPredictions?'
ONE_WEEK_STRS = ('w', '1w')
TWO_DAY_STRS = ('48h', '2d')


@dataclass
class Predictions:
    table: pd.DataFrame
    link: str


def _starts_with_one_of(s: str, candidates: str | Sequence[str], ignore_case=True) -> bool:
    if isinstance(candidates, str):
        candidates = [candidates]
    if ignore_case:
        s = s.lower()
        candidates = [c.lower() for c in candidates]
    return any([s.startswith(c) for c in candidates])


def parse_time_period(r: None | int | str) -> int:
    if r is None:
        return 1  # Default
    if isinstance(r, str):
        try:
            r = int(r)
        except ValueError:
            pass
    if isinstance(r, int):
        if r not in (1, 2):
            raise ValueError(f"Invalid integer value for range: {r}. Accepted values: {{1 = 48 hrs, 2 = Weekly}}")
        return r
    if _starts_with_one_of(r, 'w'):
        return 2
    elif not _starts_with_one_of(r, TWO_DAY_STRS):
        raise ValueError()
    return 1


def retrieve_currents_table(station_id: str, date: Optional[str] = None, time_period=None, delete=True) -> Predictions:
    if date is None:
        date = pendulum.today().format('YYYY-MM-DD')
    time_period = parse_time_period(time_period)
    csv_url_params = {'fmt': 'csv',
                      'd': date,
                      'r': time_period,  # range {1 = 48 hrs, 2 = Weekly}
                      'tz': 'LST%2fLDT',
                      'id': station_id,
                      't': 'am%2fpm'}
    csv_url = CSV_URL_BASE + '&'.join([f"{k}={v}" for k, v in csv_url_params.items()])
    csv_filename = f"current_predictions_{station_id}_{date}.csv"
    station_link = f"https://tidesandcurrents.noaa.gov/noaacurrents/Predictions?id={station_id}"
    (_, msg) = urlretrieve(csv_url, csv_filename)
    try:
        df = pd.read_csv(csv_filename)
    except:
        print(msg)
        raise
    if delete:
        os.remove(csv_filename)
    return Predictions(df, station_link)
