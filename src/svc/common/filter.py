from dataclasses import dataclass
from typing import overload

from src.svc.common import CommonEverything


@dataclass
class BaseFilter:
    @overload
    async def __call__(self, everything: CommonEverything) -> bool: 
        ...
