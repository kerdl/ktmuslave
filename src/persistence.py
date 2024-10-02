import aiofiles
from typing import Callable, Optional
from typing_extensions import Self
from pathlib import Path
from pydantic import BaseModel


class Persistence(BaseModel):
    """
    # Saves and loads JSONs
    """
    path: Optional[Path] = None
    
    async def save(self) -> None:
        path: str = self.path

        async with aiofiles.open(path, mode="w") as f:
            ser = self.model_dump_json(
                indent=2,
                exclude={"path"}
            )
            await f.write(ser)
    
    def poll_save(self) -> None:
        from src import defs
        defs.create_task(self.save())
    
    @classmethod
    def load(cls, path: Path) -> Self:
        with open(path, mode="r", encoding="utf8") as f:
            self = cls.model_validate_json(f.read())
            self.path = path

            return self

    @classmethod
    def load_or_init(cls, path: Path, init_fn: Callable[[], Self]) -> Self:
        if path.exists():
            return cls.load(path)
        else:
            self = init_fn()
            self.path = path
            self.poll_save()

            return self