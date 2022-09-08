if __name__ == "__main__":
    import sys
    sys.path.append('.')

from src.svc.common.states import State
from src.svc.common.states.tree import Tree


BULLET = "•"
ARROW_RIGHT = "→"

def tabs(level: int) -> str:
    return "  " * (level - 1)

def completed(state: State) -> str:
    return f"{state.emoji} {state.name}"

def current(state: State) -> str:
    return f"→ {state.name}"

def upcoming(state: State) -> str:
    return f"• {state.name}"

def format_tree(trace: list[State], tree: Tree, base_lvl: int = 1):
    """
    ## Convert tree to a nice readable text
    """

    formatted_states: list[str] = []
    output = ""

    current_state = trace[-1]
    last_lvl = base_lvl
    last_branch: list[State] = []
    was_in_last_branch = False

    for i, tree_state in enumerate(tree):
        tree_state: State
        is_last = (i + 1) == len(tree.__states__)

        def choose_state_format(state: State) -> str:
            if state == current_state:
                return current(state)
            elif state in trace:
                return completed(state)
            else:
                return upcoming(state)
            
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


        if was_in_last_branch:
            for branch_state in last_branch:
                state = construct_state(branch_state)
                formatted_states.append(state)
            
            last_branch = []

        if tree_state.level == base_lvl:
            state = construct_state(tree_state)
            formatted_states.append(state)

    output = "\n".join(formatted_states)

    return output


if __name__ == "__main__":
    from src.svc.common.states.tree import INIT, HUB

    print(format_tree(trace=[INIT.I_MAIN, INIT.I_GROUP, INIT.II_UNKNOWN_GROUP], tree=INIT, base_lvl=1))
    #print(format_tree(trace=[HUB.I_MAIN, HUB.II_SETTINGS, HUB.III_GROUP], tree=HUB, base_lvl=3))