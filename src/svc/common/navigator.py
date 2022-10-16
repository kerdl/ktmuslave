from __future__ import annotations
from typing import Optional, Union
from dataclasses import dataclass

from src.svc import common
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
    # Example:
    ```
    [ Init.I_MAIN, Init.I_GROUP, Init.I_SCHEDULE_BROADCAST ]
            ^                             ^
        where started                current state
    ```notpython
    """
    back_trace: list[State]
    """
    # Current state moves here when you press `Back` button
    - so you can use "Next" button
    """
    ignored: set[State]
    """
    # States that user is not supposed to get to
    """

    everything: Optional[common.CommonEverything]
    """
    # Last recieved event

    ## Used
    - to pass it to `on_enter`, `on_exit` methods of states
    """

    @classmethod
    def default(cls: type[Navigator]):
        return cls(
            trace      = [tree.Init.I_MAIN],
            back_trace = [],
            ignored    = set(),
            everything = None
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
                f"appending {state.anchor} that is ignored: {self.ignored}"
            )
        
        if self.current is state:
            raise error.DuplicateState(
                f"appending {state.anchor} that was the current one"
            )
        
        if self.current_back_trace is state:
            return self.next()

        self.append_no_checks(state)

    def append_no_checks(self, state: State):
        # we exit current state, 
        # but it will remain
        # in trace, we can go back
        # to it, so we call `on_traced_exit`
        self.current.on_traced_exit(self.everything)
    
        self.trace.append(state)

        # we entered a state
        # for the first time,
        # it wasn't in trace before,
        # so we call `on_enter`
        self.current.on_enter(self.everything)

    def back(self, trace_it: bool = True):
        """
        # Remove last state from current space

        ## Params
        - `trace_it` - if current state
        should be appended to `back_trace`
        """
        if len(self.trace) < 2:
            return None

        if trace_it and self.trace[-1].back_trace:
            self.back_trace.append(self.current)

        # this state won't be in trace
        # anymore, so we call `on_exit`
        self.current.on_exit(self.everything)

        del self.trace[-1]

        # state we just got to was
        # in trace, so we call `on_traced_enter`
        self.current.on_traced_enter(self.everything)

    def next(self):
        if len(self.back_trace) > 0:
            self.append_no_checks(self.current_back_trace)
            del self.back_trace[-1]
    
    def delete(self, state: State) -> bool:
        for (i, traced_state) in enumerate(self.trace):
            if traced_state == state:
                # MOTHERFUCKER GETS EJECTED
                traced_state.on_delete(self.everything)

                del self.trace[i]
                return True
        
        return False
    
    def delete_back_trace(self, state: State) -> bool:
        for (i, traced_state) in enumerate(self.back_trace):
            if traced_state == state:
                # MOTHERFUCKER GETS EJECTED
                traced_state.on_delete(self.everything)
    
                del self.back_trace[i]
                return True
        
        return False

    def jump_back_to(self, state: State, trace_it: bool = False):
        if state not in self.trace:
            raise error.ThisStateNotInTrace(
                "you tried to jump back to state "
                "that is not in trace"
            )
        
        while self.current != state:
            self.back(trace_it = trace_it)
    
    def jump_back_to_or_append(self, state: State, trace_it: bool = False):
        try:
            self.jump_back_to(state)
        except error.ThisStateNotInTrace:
            self.append(state)