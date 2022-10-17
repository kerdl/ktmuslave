if __name__ == "__main__":
    import sys
    sys.path.append('.')

from typing import Any, Optional

from src.svc.common import messages
from src.svc.common.navigator import Navigator
from src.svc.common.states import State, Values


def tabs(level: int) -> str:
    return "  " * (level - 1)

def add_value(original_text: str, value: Optional[Any] = None) -> str:
    if value is not None:
        return original_text + f": {value}"
    else:
        return original_text


def completed(state: State, value: Optional[Any] = None) -> str:
    text = f"✅ {state.name}"

    return add_value(text, value)

def current(state: State, value: Optional[Any] = None) -> str:
    text = f"➡️ {state.name}"

    return add_value(text, value)

def unfolded(state: State, value: Optional[Any] = None) -> str:
    text = f"⏺️ {state.name}"

    return add_value(text, value)

def upcoming(state: State, value: Optional[Any] = None) -> str:
    text = f"⬜ {state.name}"

    return add_value(text, value)

def tree(navigator: Navigator, values: Optional[Values] = None, base_lvl: int = 1):
    """
    ## Convert tree to a nice readable text
    """

    formatted_states: list[str] = []
    output = ""

    trace = navigator.trace
    ignored = navigator.ignored

    current_state = navigator.current
    tree = current_state.tree
    last_lvl = base_lvl
    last_branch: list[State] = []
    was_in_last_branch = False

    for i, tree_state in enumerate(tree):
        if tree_state in ignored:
            continue

        tree_state: State
        is_last = (i + 1) == len(tree.__states__)

        def choose_state_format(state: State) -> str:
            we_in_this_state_child_branch = False

            for child in state.child:
                if child in trace and current_state.level == child.level:
                    we_in_this_state_child_branch = True
                    break
            
            value = None

            if values:
                value = values.get_from_state(state)

                if isinstance(value, bool):
                    value = messages.value_repr(value)

            if state == current_state:
                return current(state, value)
            elif we_in_this_state_child_branch:
                return unfolded(state, value)
            elif state in trace:
                return completed(state, value)
            else:
                return upcoming(state, value)
            
        def construct_state(state: State) -> str:
            fmt = ""
            fmt += tabs(state.level)
            fmt += choose_state_format(state)

            return fmt

        def is_just_jumped_to_branch() -> bool:
            """
            Assuming `base_lvl = 1`, so base level is `I`
            - `I -> II` - True
            - `II -> I` - False, counts as RETURNING from branch
            """
            return tree_state.level > base_lvl
        
        def is_just_returned_from_branch() -> bool:
            """
            Assuming `base_lvl = 1`, so base level is `I`
            - `II -> I` - True
            - `I -> II` - False, counts as JUMPING to branch
            """
            return tree_state.level < last_lvl and tree_state.level == base_lvl

        def is_branch_in_users_path() -> bool:
            for trace_state in trace:
                if trace_state in last_branch:
                    return True
                
            return False


        if is_just_jumped_to_branch():
            last_lvl = tree_state.level
            last_branch.append(tree_state)

        if is_just_returned_from_branch() or is_last:
            was_in_last_branch = is_branch_in_users_path()

            if not was_in_last_branch:
                last_branch = []
            
            last_lvl = base_lvl


        if was_in_last_branch:
            for branch_state in last_branch:
                state = construct_state(branch_state)
                formatted_states.append(state)
            
            last_branch = []
            was_in_last_branch = False

        if tree_state.level == base_lvl:
            state = construct_state(tree_state)
            formatted_states.append(state)

    output = "\n".join(formatted_states)

    return output


if __name__ == "__main__":
    from src.svc.common.states.tree import INIT, HUB

    nav = Navigator(
        trace = [INIT.I_MAIN, INIT.I_GROUP, INIT.II_UNKNOWN_GROUP],
        back_trace = [],
        ignored = []
    )

    print(tree(nav, base_lvl=1))
