import os
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Optional, Sequence
from urllib.request import urlretrieve

import pandas as pd
import pendulum

from utils.data import rename_cols
from utils.scripts import try_main
from utils.slack import NykpSlackChannels, post_message, post_file
from utils.units import knots_to_mph

CURRENTS_CSV_URL_BASE = 'https://tidesandcurrents.noaa.gov/noaacurrents/DownloadPredictions?'
CURRENTS_CSV_DATE_FMT = 'YYYY-MM-DD'
ONE_WEEK_STRS = ('w', '1w')
TWO_DAY_STRS = ('48h', '2d')


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


@dataclass
class Station:
    name: str
    id: str
    depth: Optional[str] = None


HUDSON_RIVER_PIER_92 = Station('Hudson River, Pier 92', 'NYH1928', '6 feet')
HUDSON_RIVER_ENTRANCE = Station('Hudson River Entrance', 'NYH1927_13')
default_nykp_station = HUDSON_RIVER_PIER_92


def format_currents_table(df: pd.DataFrame, date=None) -> str:
    if date is None:
        date = pendulum.today()
    if not isinstance(date, str):
        date = date.format('YYYY-MM-DD')
    col_renames = {'Date_Time (LST/LDT)': 'datetime',
                   'Event': 'stage',
                   'Speed (knots)': 'knots'}
    df = rename_cols(df, col_renames)
    df['date'] = df['datetime'].map(lambda dts: dts.split(' ')[0])
    df['time'] = df['datetime'].map(lambda dts: ' '.join(dts.split(' ')[1:]))
    df['mph'] = df['knots'].map(knots_to_mph)
    text = ''
    today_df = df[df['date'] == date]
    for _, row in today_df.iterrows():
        text += f"{row['time']}  "
        text += row['stage']
        if pd.notna(row['mph']):
            text += f" ({row['mph']:.1f} mph)"
        text += '\n'
    return text.rstrip()


def post_currents(channel: str, station: Optional[Station] = None, date=None, time_period=None, days=1) -> None:
    if station is None:
        station = default_nykp_station
    predictions = retrieve_currents_table(station_id=station.id, date=date, time_period=time_period)
    dates = sorted(predictions.table['Date_Time (LST/LDT)'].map(lambda dt: dt.split(' ')[0]).unique())
    dates = dates[:days]
    post_txt = f"<{predictions.link}|NOAA current predictions at {station.name} (depth: {station.depth})>\n"
    for d in dates:
        table_txt = format_currents_table(predictions.table, date=d)
        date_str = pendulum.parse(d).format('dddd, MMMM D, YYYY')
        post_txt += f"*{date_str}*\n{table_txt}"
    response = post_message(post_txt, channel=channel, unfurl_links=False)
    if predictions.plot_img_path:
        file = post_file(predictions.plot_img_path, channel=channel)


"""----------------------------------------------------------------------------
SCRIPT CODE
----------------------------------------------------------------------------"""


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--station', type=str, default=None)
    parser.add_argument('--range', type=str, default=None)
    parser.add_argument('--channel', type=str, default=None)
    parser.add_argument('--days', type=int, default=1)
    return parser


def main(args):
    if args.channel is not None:
        channel = args.channel
    else:
        channel = NykpSlackChannels.test_python_api

    if args.station is not None:
        station = Station(id=args.station, name=f"Station {args.station}")
    else:
        station = None

    post_currents(channel, station=station, date=args.date, time_period=args.range)


if __name__ == '__main__':
    parser = parse_args()
    try_main(main, parser)
