from typing import Optional
from dataclasses import dataclass

from src.svc.common import error
from src.svc.common.states import State, SPACE_LITERAL


@dataclass
class Navigator:
    """
    ## Traces user's path between states
    So he can use `← Back` button
    """

    trace: list[State]
    """
    ## Example:
    ```
        [ Init.I_MAIN, Init.I_GROUP, Init.I_SCHEDULE_BROADCAST ]
                ^                             ^
            where started                current state
    ```notpython
    """

    @property
    def current(self) -> Optional[State]:
        """
        ## Last state from `trace`
        """
        if len(self.trace) < 1:
            return None

        return self.trace[-1]

    @property
    def space(self) -> SPACE_LITERAL:
        """
        ## Get space of current state
        """
        return self.current.space

    def append(self, state: State):
        """
        ## Add state to trace

        ## Raises errors:
        - `SpaceMixing` when trying to add
        state with different type of space
        """
        if state.space != self.space:
            raise error.SpaceMixing(
                f"tried to append {state.space} state to {self.space} trace"
            )

        self.trace.append(state)

    def back(self):
        """
        ## Remove last state from current space
        """
        if len(self.trace) > 1:
            del self.trace[-1]
