from __future__ import annotations
from typing import Optional, Union
from dataclasses import dataclass

from src.svc.common import error
from src.svc.common.states import State, SPACE_LITERAL, tree


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

    @classmethod
    def default(cls: type[Navigator]):
        return cls(
            trace      = [tree.Init.I_MAIN],
            back_trace = [],
            ignored    = set()
        )

    @property
    def current(self) -> Optional[State]:
        """
        ## Last state from `trace`
        """
        if len(self.trace) < 1:
            return None

        return self.trace[-1]

    @property
    def current_back_trace(self) -> Optional[State]:
        """
        ## Last state from `back_trace`
        """
        if len(self.back_trace) < 1:
            return None
        
        return self.back_trace[-1]

    @property
    def space(self) -> SPACE_LITERAL:
        """
        ## Get space of current state
        """
        return self.current.space

    def append(self, state: State):
        """ ## Add state to trace """
        if state in self.ignored:
            raise error.GoingToIgnoredState(
                f"appending {state.name} that is ignored: {self.ignored}"
            )
        
        if self.current_back_trace is state:
            return self.next()
        
        if self.current is state:
            raise error.DuplicateState(
                f"appending {state.name} that was the current one"
            )

        self.trace.append(state)

    def append_no_checks(self, state: State):
        self.trace.append(state)

    def back(self, trace_it: bool = True):
        """
        ## Remove last state from current space
        """
        if len(self.trace) < 2:
            return None

        if trace_it and self.trace[-1].back_trace:
            self.back_trace.append(self.current)

        del self.trace[-1]
    
    def next(self):
        if len(self.back_trace) > 0:
            last_back_state = self.back_trace[-1]
            self.append_no_checks(last_back_state)

            del self.back_trace[-1]
    
    def delete(self, state: State) -> bool:
        for (i, traced_state) in enumerate(self.trace):
            if traced_state == state:
                del self.trace[i]
                return True
        
        return False
    
    def delete_back_trace(self, state: State) -> bool:
        for (i, traced_state) in enumerate(self.back_trace):
            if traced_state == state:
                del self.back_trace[i]
                return True
        
        return False
