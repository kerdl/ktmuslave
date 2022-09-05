if __name__ == "__main__":
    import sys
    sys.path.append('.')

from enum import Enum
from src.svc.common.states import State


def level(state):
    return len(state.name.split("_")[0])

def format_tree(trace: list[State]):
    """
    ## Convert tree to a nice readable text
    """

    output = ""

    tree: Enum = type(trace[0])
    current_state = trace[-1]

    ignore_found_current = False

    tree_level_traceback = []
    for tree_state in tree:
        current_tree_lvl = level(tree_state)
        tabs = "  " * (current_tree_lvl - 1)

        if len(tree_level_traceback) > 0 and (
            level(tree_level_traceback[-1]) >= current_tree_lvl
        ):
            tree_level_traceback = []
        
        tree_level_traceback.append(tree_state)

        class Props:
            completed = False
            found_current = False
            in_branch = False

        def check_in_branch():
            if trace_state in tree_level_traceback:
                Props.in_branch = True

        for trace_state in trace:
            if (not ignore_found_current) and (
                trace_state == tree_state == current_state
            ):
                ignore_found_current = True
                Props.found_current = True

                check_in_branch()
                break

            elif trace_state == tree_state:
                Props.completed = True

                check_in_branch()
                break
                
            check_in_branch()

        if Props.in_branch:
            output += tabs

            if Props.completed:
                output += f"{tree_state.value.emoji} "
            elif Props.found_current:
                output += "→ "
            elif Props.in_branch:
                output += "• "

            output += f"{tree_state.value.name}\n"
        
    return output


if __name__ == "__main__":
    from src.svc.common.states.tree import Init

    print(format_tree([Init.I_MAIN, Init.I_GROUP, Init.I_SCHEDULE_BROADCAST]))