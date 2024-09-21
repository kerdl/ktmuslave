import datetime
from aiohttp import ClientResponse
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel
from src.data import RepredBaseModel
from src.data.duration import Duration
from src.data.schedule import Page
from src.data.schedule.compare import PageCompare


class Error(BaseModel):
    ...

class Notify(BaseModel):
    random: str
    groups: Optional[PageCompare]
    teachers: Optional[PageCompare]
    
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
    
    def has_updates_for_teacher(self, name: str):
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
    last: Optional[datetime.datetime]
    period: Optional[Duration]

class Data(BaseModel):
    page: Optional[Page]
    updates: Optional[Updates]

class Response(BaseModel):
    is_ok: bool
    data: Optional[Data]
    error: Optional[Error]

async def request(
    url: str,
    method: Callable[[str], Awaitable[ClientResponse]],
    return_result: bool = True
):
    resp = await method(url)
    resp_text = await resp.text()

    if return_result:
        response = Response.parse_raw(resp_text)
        return response

async def get(url: str, return_result: bool = True):
    from src import defs
    return await request(url, defs.http.get, return_result=return_result)

async def post(url: str):
    from src import defs
    return await request(url, defs.http.post)