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
    back_trace: list[State]
    """
    ## Current state moves here when you press `Back` button
    - so you can use "Next" button
    """
    ignored: set[State]
    """
    ## States that user is not supposed to get to
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
        """ ## Add state to trace """
        self.trace.append(state)

    def back(self):
        """
        ## Remove last state from current space
        """
        if len(self.trace) > 1:
            self.back_trace.append(self.current)

            del self.trace[-1]
    
    def next(self):
        if len(self.back_trace) > 0:
            last_back_state = self.back_trace[-1]
            self.append(last_back_state)

            del self.back_trace[-1]
