from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")

class Range(BaseModel, Generic[T]):
    start: T
    end: T