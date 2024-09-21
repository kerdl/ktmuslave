from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Literal
from pathlib import Path
import aiofiles


class Tokens(BaseModel):
    vk: Optional[str]
    tg: Optional[str]

class Server(BaseModel):
    addr: str

class Database(BaseModel):
    addr: str
    password: Optional[str]

class Admins(BaseModel):
    id: int
    src: Literal["vk", "tg"]

class Logging(BaseModel):
    enabled: bool
    dir: Optional[Path]
    admins: list[Admins]

class Urls(BaseModel):
    schedules: Optional[str]
    journals: Optional[str]
    materials: Optional[str]

class TimeSchedule(BaseModel):
    name: str
    nums: dict[str, str]

class TimeMapping(BaseModel):
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str

class Time(BaseModel):
    schedules: list[TimeSchedule]
    mapping: Optional[str]

class Settings(BaseModel):
    path: Optional[Path]
    tokens: Tokens
    server: Server
    database: Database
    logging: Optional[Logging]
    urls: Optional[Urls]
    time: Optional[Time]

    async def save(self):
        path: str = self.path

        async with aiofiles.open(path, mode="w") as f:
            ser = self.model_dump_json(
                ensure_ascii=False,
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
            self = cls.model_validate_json(f.read())
            self.path = path

            return self

    @classmethod
    def load_or_init(cls: type[Settings], path: Path) -> Settings:
        if path.exists():
            return cls.load(path)
        else:
            self = cls(
                path=path,
                tokens=Tokens(vk="", tg=""),
                server=Server(addr=""),
                database=Database(addr=""),
                logging=Logging(enabled=False, admins=[]),
                urls=Urls()
            )
            self.poll_save()

            return self
    