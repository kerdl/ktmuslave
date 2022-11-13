from typing import Optional
from pydantic import BaseModel
import datetime

from src.data import Duration
from src.data.schedule import Page
from src.api import schedule


class Error(BaseModel):
    ...

class Data(BaseModel):
    page: Optional[Page]
    interactor: Optional[schedule.Interactor]
    notify: Optional[schedule.Notify]
    url: Optional[str]
    period: Optional[Duration]
    last_update: Optional[datetime.datetime]

class Response(BaseModel):
    is_ok: bool
    data: Optional[Data]
    error: Optional[Error]
