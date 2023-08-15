from dataclasses import dataclass, fields
from datetime import datetime
from typing import Self

import feedparser
import pendulum
import pytz

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
