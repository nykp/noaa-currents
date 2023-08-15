import pdb
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timedelta
from traceback import print_exception
from typing import Optional

import numpy as np
import pandas as pd
import pendulum
import pytz

from utils.data import rename_cols
from utils.noaa import retrieve_currents_table
from utils.notify_nyc import get_waterbody_advisories
from utils.slack import NykpSlackChannels, post_message, post_file


@dataclass
class Station:
    name: str
    id: str
    depth: Optional[str] = None


HUDSON_RIVER_PIER_92 = Station('Hudson River, Pier 92', 'NYH1928', '6 feet')
HUDSON_RIVER_ENTRANCE = Station('Hudson River Entrance', 'NYH1927_13')
default_nykp_station = HUDSON_RIVER_PIER_92


def knots_to_mph(knots) -> Optional[float]:
    try:
        if isinstance(knots, str):
            knots = float(knots)
        return knots * 1.15078
    except (TypeError, ValueError):
        return np.nan


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


def post_waterbody_advisories(
        channel: str,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
        days=1
):
    if isinstance(end_time, str):
        end_time = pendulum.parse(end_time)
    elif end_time is None:
        end_time = datetime.now(tz=pytz.timezone('America/New_York'))

    if isinstance(start_time, str):
        start_time = pendulum.parse(start_time)
    elif start_time is None:
        start_time = end_time - timedelta(days=days)

    advisories = get_waterbody_advisories(start_dt=start_time, end_dt=end_time)
    for advisory in advisories:
        response = post_message(advisory.print(), channel=channel)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--station', type=str, default=None)
    parser.add_argument('--range', type=str, default=None)
    parser.add_argument('--channel', type=str, default=None)
    parser.add_argument('--days', type=int, default=1)
    parser.add_argument('--pdb', action='store_true')
    args = parser.parse_args()

    if args.pdb:
        pdb.set_trace()

    if args.channel is not None:
        channel = args.channel
    else:
        channel = NykpSlackChannels.test_python_api

    if args.station is not None:
        station = Station(id=args.station, name=f"Station {args.station}")
    else:
        station = None

    try:
        post_currents(channel, station=station, date=args.date, time_period=args.range)
        post_waterbody_advisories(channel, days=args.days)
    except Exception as e:
        print_exception(e)
        pdb.post_mortem()
