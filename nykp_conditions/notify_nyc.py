from argparse import ArgumentParser

from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from typing import Optional, Self

import feedparser
import pendulum
import pytz

from utils.scripts import try_main
from utils.slack import NykpSlackChannels, post_message


NOTIFY_NYC_URL = 'https://a858-nycnotify.nyc.gov/RSS/NotifyNYC?lang=en'
WATERBODY_ADVISORY = 'Waterbody Advisory'
ALERTS_FIELD = 'entries'
NOTIFY_DATE_FMT = '%m/%d/%Y %H:%M:%S'
NOTIFY_NYC_TZ = pytz.timezone('America/New_York')


@dataclass
class NotifyAlert:
    title: str
    published: datetime
    summary: str

    def __post_init__(self):
        if isinstance(self.published, str):
            try:
                self.published = datetime.strptime(self.published, NOTIFY_DATE_FMT).replace(tzinfo=NOTIFY_NYC_TZ)
            except ValueError:
                self.published = pendulum.parse(self.published)

    @classmethod
    def parse(cls, entry: dict) -> Self:
        field_names = [f.name for f in fields(cls)]
        kws = {field: entry.get(field) for field in field_names}
        return cls(**kws)

    def print(self) -> str:
        return f"{self.published} -- {self.title}\n\n{self.summary}"


def get_waterbody_advisories(
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
        url: str = NOTIFY_NYC_URL,
) -> list[NotifyAlert]:
    
    def f(alert: NotifyAlert) -> bool:
        if WATERBODY_ADVISORY not in alert.title:
            return False
        if start_dt and alert.published < start_dt:
            return False
        if end_dt and alert.published > end_dt:
            return False
        return True
    
    feed = feedparser.parse(url)
    alerts = map(NotifyAlert.parse, feed[ALERTS_FIELD])
    return list(filter(f, alerts))


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


"""----------------------------------------------------------------------------
SCRIPT CODE
----------------------------------------------------------------------------"""


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--channel', type=str, default=None)
    parser.add_argument('--days', type=int, default=1)
    return parser


def main(args):
    if args.channel is not None:
        channel = args.channel
    else:
        channel = NykpSlackChannels.test_python_api
    post_waterbody_advisories(channel, days=args.days)


if __name__ == '__main__':
    parser = parse_args()
    try_main(main, parser)
