from __future__ import annotations
import aiofiles
import datetime
from typing import Optional
from pathlib import Path
from pydantic import BaseModel
from src.data import week
from src.data.range import Range


BASE_WEEKDAY = 6


class WeekCast(BaseModel):
    path: Optional[Path] = None
    covered: Optional[Range[datetime.date]] = None

    async def save(self):
        path: str = self.path

        async with aiofiles.open(path, mode="w") as f:
            ser = self.model_dump_json(
                indent=2,
                exclude={"path"}
            )
            await f.write(ser)
    
    def poll_save(self):
        from src import defs
        defs.create_task(self.save())
    
    @classmethod
    def load(cls, path: Path):
        with open(path, mode="r", encoding="utf8") as f:
            made_changes = False
            self = cls.model_validate_json(f.read())
            self.path = path
            
            if self.covered is None:
                self.covered = week.cover_today(idx=BASE_WEEKDAY)
                made_changes = True
            
            if made_changes:
                self.poll_save()

            return self

    @classmethod
    def load_or_init(cls: type[WeekCast], path: Path) -> WeekCast:
        if path.exists():
            return cls.load(path)
        else:
            covered = week.cover_today(idx=BASE_WEEKDAY)
            self = cls(
                path=path,
                covered=Range[datetime.date](
                    start=covered.start,
                    end=covered.end
                )
            )
            self.poll_save()

            return self