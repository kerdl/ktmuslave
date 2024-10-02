from __future__ import annotations
import aiofiles
import datetime
from typing import Optional
from typing_extensions import Self
from pathlib import Path
from src.data import week
from src.data.range import Range
from src.persistence import Persistence


BASE_WEEKDAY = 6


class WeekCast(Persistence):
    covered: Optional[Range[datetime.date]] = None

    @classmethod
    def load(cls, path: Path) -> Self:
        this = super().load(path)
        if this.covered is None:
            covered = week.cover_today(idx=BASE_WEEKDAY)
            this.covered = Range[datetime.date](
                start=covered.start,
                end=covered.end
            )
            this.poll_save()
        return this

    @classmethod
    def load_or_init(cls: type[WeekCast], path: Path) -> Self:
        covered = week.cover_today(idx=BASE_WEEKDAY)
        init_fn = lambda: WeekCast(covered=Range[datetime.date](start=covered.start, end=covered.end))
        return super().load_or_init(path=path, init_fn=init_fn)