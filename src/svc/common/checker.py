from svc.common.navigator import Navigator
from svc.common.states import State
from svc.common.states.tree import Space


async def is_user_on_state(navigator: Navigator, state: State) -> bool:
    is_user_on_this_state = False

    match state.space:
        case Space.INIT:
            is_user_on_this_state = (
                navigator.current_init == state
            )
        case Space.HUB:
            is_user_on_this_state = (
                navigator.current_hub == state
            )
    
    return is_user_on_this_state