from svc.common.navigator import Navigator
from svc.common.states import State
from svc.common.states.tree import Space


async def is_user_on_state(navigator: Navigator, state: State) -> bool:
    return navigator.current == state