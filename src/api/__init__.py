from typing import Optional
from pydantic import BaseModel

from src.data.schedule import Page
from src.api import schedule


class Error(BaseModel):
    ...

class Data(BaseModel):
    page: Optional[Page]
    interactor: Optional[schedule.Interactor]
    notify: Optional[schedule.Notify]

class Response(BaseModel):
    is_ok: bool
    data: Optional[Data]
    error: Optional[Error]
