from src.svc.common.navigator import Navigator
from src.svc.common.states import State
from src.svc.common.states.tree import Space


async def is_user_on_state(navigator: Navigator, state: State) -> bool:
    return navigator.current == state