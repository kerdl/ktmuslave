from loguru import logger
from typing import Optional, Literal, Union
from dataclasses import dataclass
from pydantic import BaseModel
from websockets import client, exceptions
from websockets.legacy import client

from src import defs
from src.api.base import Api
from src.data.schedule import Page, compare


AUTO_LITERAL = Literal["auto"]


class Interactor(BaseModel):
    key: str

class Ivoker(BaseModel):
    manually: Interactor

class Notify(BaseModel):
    invoker: Union[AUTO_LITERAL, Ivoker]
    daily: Optional[compare.PageCompare]
    weekly: Optional[compare.PageCompare]

@dataclass
class ScheduleApi(Api):
    interactor: Optional[Interactor]

    last_daily: Optional[Page]
    last_weekly: Optional[Page]

    async def schedule(self, url: str) -> Page:
        from src.api import Response

        resp = await defs.http.get(url)
        text = await resp.text()

        response = Response.parse_raw(text)

        return response.data.page

    async def daily(self) -> Page:
        url = "http://" + self.url + "/daily"
        self.last_weekly = await self.schedule(url)

        return self.last_daily
    
    async def weekly(self) -> Page:
        url = "http://" + self.url + "/weekly"
        self.last_weekly = await self.schedule(url)

        return self.last_weekly

    async def cached_daily(self) -> Page:
        if self.last_daily is None:
            return await self.daily()

        return self.last_daily

    async def cached_weekly(self) -> Page:
        if self.last_weekly is None:
            return await self.weekly()

        return self.last_weekly

    async def interact(self) -> Interactor:
        from src.api import Response

        url = "http://" + self.url + "/interact"

        logger.info("getting schedule updates key")

        resp = await defs.http.get(url)
        text = await resp.text()

        response = Response.parse_raw(text)

        self.interactor = response.data.interactor

        logger.info(f"we got key {self.interactor.key}")

        return self.interactor

    async def interactor_valid(self) -> bool:
        from src.api import Response

        url = "http://" + self.url + f"/interact/is-valid?key={self.interactor.key}"

        resp = await defs.http.get(url)
        text = await resp.text()

        response = Response.parse_raw(text)

        return response.is_ok

    async def updates(self):
        if self.interactor is None or not await self.interactor_valid():
            await self.interact()
        
        url = "ws://" + self.url + f"/updates?key={self.interactor.key}"

        def protocol_factory(*args, **kwargs) -> client.WebSocketClientProtocol:
            protocol = client.WebSocketClientProtocol()
            protocol.max_size = 2**48
            protocol.read_limit = 2**48

            return protocol

        logger.info(f"connecting to {url}")
        async with client.connect(url, create_protocol=protocol_factory) as socket:
            try:
                logger.info(f"awaiting updates...")
                async for message in socket:
                    notify = Notify.parse_raw(message)

                    await self.daily()
                    await self.weekly()
            except exceptions.ConnectionClosedError as e:
                logger.info(e)
                logger.info("reconnecting...")
                return await self.updates()

    async def update(self):
        from src.api import Response

        if self.interactor is None or not await self.interactor_valid():
            await self.interact()

        url = "http://" + self.url + f"/update?key={self.interactor.key}"

        resp = await defs.http.post(url)
        text = await resp.text()

        response = Response.parse_raw(text)

        return response

SCHEDULE_API = ScheduleApi("localhost:8080/schedule", None)