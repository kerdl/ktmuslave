from pydantic import BaseModel


class Duration(BaseModel):
    secs: int
    nanos: int

    def __str__(self) -> str:
        """As minutes"""
        return str(int(self.secs / 60))