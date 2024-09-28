from __future__ import annotations

import datetime
from aiohttp import ClientResponse
from typing import Optional, Callable, Awaitable, TYPE_CHECKING
from typing_extensions import Self
from pydantic import BaseModel
from src.data.duration import Duration
from src.data.schedule import Page, Weeked
from src.data.schedule.compare import PageCompare
from src.data.range import Range


if TYPE_CHECKING:
    from src.data import RepredBaseModel


class Error(BaseModel):
    ...


class Notify(BaseModel):
    random: str
    groups: Optional[PageCompare] = None
    teachers: Optional[PageCompare] = None
    
    def _chunk_formations_by_week(self) -> None:
        try:
            self.groups._chunk_formations_by_week()
            self.teachers._chunk_formations_by_week()
        except AttributeError:
            ...
    
    def get_week_self(self, rng: Range[datetime.date]) -> Self:
        return Notify(
            random=self.random,
            groups=self.groups.get_week_self(rng) if self.groups else None,
            teachers=self.teachers.get_week_self(rng) if self.teachers else None
        )
    
    def has_updates_for_group(self, name: str) -> bool:
        if self.groups is None:
            return False
        
        for change in [
            self.groups.formations.appeared,
            self.groups.formations.changed
        ]:
            for formation in change:
                formation: RepredBaseModel
                if formation.repr_name == name:
                    return True
        
        return False
    
    def has_updates_for_teacher(self, name: str) -> bool:
        if self.teachers is None:
            return False
        
        for change in [
            self.teachers.formations.appeared,
            self.teachers.formations.changed
        ]:
            for formation in change:
                formation: RepredBaseModel
                if formation.repr_name == name:
                    return True
        
        return False


class Updates(BaseModel):
    last: Optional[datetime.datetime] = None
    period: Optional[Duration] = None


class Data(BaseModel):
    page: Optional[Page] = None
    updates: Optional[Updates] = None


class Response(BaseModel):
    is_ok: bool
    data: Optional[Data] = None
    error: Optional[Error] = None


async def request(
    url: str,
    method: Callable[[str], Awaitable[ClientResponse]],
    return_result: bool = True
):
    resp = await method(url)
    resp_text = await resp.text()

    if return_result:
        response = Response.model_validate_json(resp_text)
        return response


async def get(url: str, return_result: bool = True):
    from src import defs
    return await request(url, defs.http.get, return_result=return_result)


async def post(url: str):
    from src import defs
    return await request(url, defs.http.post)