from __future__ import annotations

import asyncio
import datetime
from loguru import logger
from typing import Optional, Never
from typing_extensions import Self
from pathlib import Path
from dataclasses import dataclass
from websockets import client, exceptions
from websockets.legacy import client
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ServerDisconnectedError
)
from src.api import get, Notify
from src.data import week
from src.data.schedule import Page
from src.data.duration import Duration
from src.persistence import Persistence


class LastNotify(Persistence):
    """
    # Info abould last `Notify` received
    """
    random: Optional[str] = None
    """
    # Last received `random`
    
    When the bot is restarted,
    ktmuscrap always sends last `Notify`
    it had generated.
    
    If that `Notify` had changes,
    a duplicate broadcast will occur,
    which is undesirable.
    
    To avoid that, we store the last
    `random` value to then ignore
    any incoming `Notify` with that value.
    """

    @classmethod
    def load_or_init(cls, path: Path) -> Self:
        init_fn = lambda: cls(random=None)
        return super().load_or_init(path=path, init_fn=init_fn)
    
    def set_random(self, random: str):
        self.random = random
        self.poll_save()

@dataclass
class ScheduleApi:
    addr: str
    """
    # Address of a running ktmuscrap instance
    """
    is_online: bool = False
    """
    # Is the server online
    Updated in real-time.
    """
    is_cached_available: bool = False
    """
    # Are schedules and data ready
    This is set to `True` at startup,
    once all data is transferred from the server.
    """
    last_notify: Optional[LastNotify] = None
    """
    # Info about last `Notify` received
    """
    ready_channel: Optional[asyncio.Queue] = None
    """
    # A "ready" event channel
    Firing once all data is ready.
    """

    _cached_groups: Optional[Page] = None
    _cached_teachers: Optional[Page] = None

    _cached_last_update: Optional[datetime.datetime] = None
    _cached_update_period: Optional[Duration] = None

    async def schedule_from_url(self, url: str) -> Optional[Page]:
        response = await get(url)
        if response.data is None:
            return None

        return response.data.page

    async def request_groups(self) -> Page:
        """
        # Request groups schedule and cache it
        """
        url = "http://" + self.addr + "/schedule/groups"
        self._cached_groups = await self.schedule_from_url(url)
        return self._cached_groups
        
    async def request_teachers(self) -> Page:
        """
        # Request teachers schedule and cache it
        """
        url = "http://" + self.addr + "/schedule/teachers"
        self._cached_teachers = await self.schedule_from_url(url)
        return self._cached_teachers

    async def request_last_update(self) -> datetime.datetime:
        """
        # Request last update time and cache it
        """
        url = "http://" + self.addr + "/schedule/updates/last"
        self._cached_last_update = (await get(url)).data.updates.last
        return self._cached_last_update

    async def request_update_period(self) -> Page:
        """
        # Request update period and cache it
        """
        url = "http://" + self.addr + "/schedule/updates/period"
        self._cached_update_period = (await get(url)).data.updates.period
        return self._cached_update_period
    
    async def request_all(self):
        """
        # Request all data and cache it
        """
        await self.request_groups()
        try: self._cached_groups._chunk_formations_by_week()
        except AttributeError: ...
        
        await self.request_teachers()
        try: self._cached_teachers._chunk_formations_by_week()
        except AttributeError: ...
        
        await self.request_last_update()
        await self.request_update_period()
    
    def get_groups(self) -> Optional[Page]:
        return self._cached_groups

    def get_teachers(self) -> Optional[Page]:
        return self._cached_teachers

    def get_last_update(self) -> Optional[datetime.datetime]:
        return self._cached_last_update

    def get_update_period(self) -> Optional[Duration]:
        return self._cached_update_period

    def group_names(self) -> list[str]:
        """
        # Group names present in the schedule
        """
        page = self.get_groups()
        if page is None: return []
        return page.names()
    
    def teacher_names(self) -> list[str]:
        """
        # Teacher names present in the schedule
        """
        page = self.get_teachers()
        if page is None: return []
        return page.names()

    async def updates(self) -> Never:
        """
        # Listen to updates
        """
        from src import defs

        retry_period = 5
        is_connection_attempt_logged = False
        is_connect_error_logged = False
        url = "ws://" + self.addr + f"/schedule/updates"
    
        while True:
            try:
                def protocol_factory(
                    *args,
                    **kwargs
                ) -> client.WebSocketClientProtocol:
                    protocol = client.WebSocketClientProtocol()
                    protocol.max_size = 2**48
                    protocol.read_limit = 2**48

                    return protocol

                if not is_connection_attempt_logged:
                    logger.info(f"connecting to {url}")
                    is_connection_attempt_logged = True

                async with client.connect(
                    url,
                    create_protocol=protocol_factory
                ) as socket:
                    try:
                        await self.request_all()

                        self.is_online = True
                        self.is_cached_available = True
                        is_connect_error_logged = False
                        is_connection_attempt_logged = False
                        await self.ready_channel.put(True)

                        logger.info(f"awaiting schedule updates...")
                        async for message in socket:
                            notify = Notify.model_validate_json(message)

                            if notify.random == self.last_notify.random:
                                logger.info(
                                    f"caught duplicate notify {notify.random}, ignoring"
                                )
                                continue

                            # update data cache
                            await self.request_all()

                            notify._chunk_formations_by_week()
                            current_active_week = week.current_active()
                            notify = notify.get_week_self(current_active_week)
                            self.last_notify.set_random(notify.random)
                            
                            if not notify.is_eligible_for_broadcast():
                                logger.info(
                                    f"notify {notify.random} is not eligible "
                                    f"for broadcasting, ignoring"
                                )
                                continue

                            await defs.check_redisearch_index()
                            await defs.ctx.broadcast(notify)
                    except exceptions.ConnectionClosedError as e:
                        logger.info(e)
                        logger.info("reconnecting to ktmuscrap...")
                        continue
            except (
                ConnectionRefusedError,
                ClientConnectorError,
                ServerDisconnectedError,
                TimeoutError
            ) as e:
                if not is_connect_error_logged:
                    self.is_online = False

                    logger.error(
                        f"error occured in a schedule update loop: "
                        f"{type(e).__name__}({e}), reconnecting..."
                    )

                    is_connect_error_logged = True
        
                await asyncio.sleep(retry_period)
                continue
