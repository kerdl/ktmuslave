from typing import Any, Optional, TYPE_CHECKING

from src.data import format as fmt
from src.svc.common.navigator import Navigator
from src.svc.common.states import State, Values

if TYPE_CHECKING:
    from src.svc.common import CommonEverything


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

def tree(
    navigator: Navigator,
    everything: "CommonEverything",
    values: Optional[Values] = None,
    base_lvl: int = 1
):
    """
    ## Convert tree to a nice readable text
    """

    formatted_states: list[str] = []
    output = ""

    trace = navigator.trace
    ignored = navigator.ignored

    current_state = navigator.current
    tree = navigator.current_tree
    last_lvl = base_lvl
    last_branch: list[State] = []
    was_in_last_branch = False

    for i, tree_state in enumerate(tree.__states__):
        if tree_state in ignored:
            continue

        if not tree_state.should_display_in_tree(everything):
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

                if value is not None:
                    value = fmt.value_repr(value)

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
            fmt += tabs(state.level - (base_lvl - 1))
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
