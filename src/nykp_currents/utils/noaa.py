from collections.abc import Sequence
from dataclasses import dataclass
import os
from typing import Optional
from urllib.request import urlretrieve

import pandas as pd
import pendulum

CURRENTS_CSV_URL_BASE = 'https://tidesandcurrents.noaa.gov/noaacurrents/DownloadPredictions?'
CURRENTS_CSV_DATE_FMT = 'YYYY-MM-DD'
ONE_WEEK_STRS = ('w', '1w')
TWO_DAY_STRS = ('48h', '2d')

TEMPS_CSV_URL_TEMPLATE = ('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=water_temperature'
                          '&application=NOS.COOPS.TAC.PHYSOCEAN&begin_date={start_date}&end_date={end_date}'
                          '&station={station_id}&time_zone=lst_ldt&units=english&interval=6&format=csv')


@dataclass
class CurrentsPredictions:
    table: pd.DataFrame
    link: str
    plot_img_path: Optional[str] = None


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


def retrieve_currents_table(
        station_id: str,
        date: str | pendulum.DateTime | None = None,
        time_period=None,
        delete=True,
) -> CurrentsPredictions:
    if date is None:
        date = pendulum.today()
    elif isinstance(date, str):
        date = pendulum.parse(date)

    # Get csv of data
    time_period = parse_time_period(time_period)
    csv_url_params = {'fmt': 'csv',
                      'd': date.format(CURRENTS_CSV_DATE_FMT),
                      'r': time_period,  # range {1 = 48 hrs, 2 = Weekly}
                      'tz': 'LST%2fLDT',
                      'id': station_id,
                      't': 'am%2fpm'}
    csv_url = CURRENTS_CSV_URL_BASE + '&'.join([f"{k}={v}" for k, v in csv_url_params.items()])
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
    return CurrentsPredictions(df, station_link)


def retrieve_water_temps_table(
        station_id: str,
        date: Optional[str | pendulum.DateTime] = None,
        time_period=None,
        delete=True,
):
    pass
