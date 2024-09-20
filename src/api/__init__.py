from typing import Optional
from pydantic import BaseModel
import datetime

from src.data import Duration
from src.data.schedule import Page, TchrPage
from src.api import schedule


class Error(BaseModel):
    ...

class Updates(BaseModel):
    last: Optional[datetime.datetime]
    period: Optional[Duration]

class Data(BaseModel):
    page: Optional[Page]
    notify: Optional[schedule.Notify]
    updates: Optional[Updates]

class Response(BaseModel):
    is_ok: bool
    data: Optional[Data]
    error: Optional[Error]
