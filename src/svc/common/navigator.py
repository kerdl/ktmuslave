from __future__ import annotations
from typing import Optional, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel

from src.svc import common
from src.svc.common import error
from src.svc.common import states
from src.svc.common.states import State, SPACE_LITERAL, tree


class DbNavigator(BaseModel):
    trace: list[str]
    back_trace: list[str]
    ignored: list[str]

    @classmethod
    def from_runtime(cls: type[DbNavigator], navigator: Navigator) -> DbNavigator:
        return cls(
            trace=[str(state) for state in navigator.trace],
            back_trace=[str(state) for state in navigator.back_trace],
            ignored=[str(state) for state in navigator.ignored]
        )
    
    def to_runtime(self, everything: Optional[common.CommonEverything] = None) -> Navigator:
        return Navigator.from_db(self, everything)

@dataclass
class Navigator:
    """
    ## Traces user's path between states
    So he can use `← Back` button
    """

    trace: list[State] = field(default_factory=lambda: [tree.INIT.I_MAIN])
    """
    # Example:
    ```
    [ Settings.I_MAIN, Settings.II_GROUP, Settings.I_BROADCAST ]
            ^                             ^
        where started                current state
    ```notpython
    """
    back_trace: list[State] = field(default_factory=list)
    """
    # Current state moves here when you press `Back` button
    - so you can use "Next" button
    """
    ignored: set[State] = field(default_factory=set)
    """
    # States that user is not supposed to get to
    """

    everything: Optional[common.CommonEverything] = None
    """
    # Last received event

    ## Used
    - to pass it to `on_enter`, `on_exit` methods of states
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
    def current_tree(self) -> tree.Tree:
        return getattr(tree, self.current.tree.upper())

    @property
    def first(self) -> Optional[State]:
        if len(self.trace) < 1:
            return None
        
        return self.trace[0]

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

    @property
    def previous_space(self) -> SPACE_LITERAL:
        for state in reversed(self.trace):
            if state.space != self.space:
                return state.space
        
        return self.space

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
        if self.current:
            self.current.on_traced_exit(self.everything)
    
        self.trace.append(state)

        # we entered a state
        # for the first time,
        # it wasn't in trace before,
        # so we call `on_enter`
        self.current.on_enter(self.everything)

    def back(
        self, 
        trace_it: bool = True,
        execute_actions: bool = True
    ):
        """
        # Remove last state from current space

        ## Params
        - `trace_it` - if current state
        should be appended to `back_trace`
        - `execute_actions` - we can assign
        actions to do when we enter/exit
        specific state. This parameter
        tells if we should execute them
        """
        if len(self.trace) < 2:
            return None

        if trace_it and self.trace[-1].back_trace:
            self.back_trace.append(self.current)

        if execute_actions:
            # this state won't be in trace
            # anymore, so we call `on_exit`
            self.current.on_exit(self.everything)

        del self.trace[-1]

        if execute_actions:
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

    def delete_back_trace_fn(self, fn: Callable[[State], bool], do_short: bool = True) -> bool:
        result = False
        for (i, traced_state) in enumerate(self.back_trace):
            if fn(traced_state):
                # MOTHERFUCKER GETS EJECTED
                traced_state.on_delete(self.everything)
    
                del self.back_trace[i]
                result = True
                if do_short:
                    return result
        
        return result
    
    def replace_back_trace(self, map: dict[str, State]):
        result = False
        for (i, traced_state) in enumerate(self.back_trace):
            target = map.get(traced_state.anchor)

            if not target:
                continue
            
            self.back_trace[i] = target
            result = True
        
        return result

    @property
    def spaces(self) -> set[SPACE_LITERAL]:
        unique_spaces: set[SPACE_LITERAL] = set()

        for state in self.trace:
            unique_spaces.add(state.space)
        
        return unique_spaces

    def is_space_mixed(self) -> bool:        
        return len(self.spaces) > 1

    def jump_back_to(
        self, 
        state: State, 
        trace_it: bool = False, 
        execute_actions: bool = True
    ):
        if state not in self.trace:
            raise error.ThisStateNotInTrace(
                "you tried to jump back to state "
                "that is not in trace"
            )
        
        if self.current == state:
            self.back(
                trace_it = False,
                execute_actions = execute_actions
            )

        while self.current != state:
            self.back(
                trace_it = trace_it, 
                execute_actions = execute_actions
            )
    
    def space_jump_back(self, trace_it: bool = False):
        if not self.is_space_mixed():
            raise error.NotSpaceMixed(
                "jumping back from current space to other isn't possible, "
                "'cause there's only one type of space in trace"
            )

        initial_space = self.space

        while initial_space == self.space:
            self.back(trace_it = trace_it)
    
    def jump_back_to_or_append(self, state: State, trace_it: bool = False):
        try:
            self.jump_back_to(state, trace_it = trace_it)
        except error.ThisStateNotInTrace:
            self.append(state)
    
    def clear_all(self) -> None:
        self.trace = []
        self.back_trace = []
        self.ignored = set()

    def clear_back_trace(self) -> None:
        self.back_trace = []
    
    def set_everything(self, everything: common.CommonEverything):
        should_auto_ignore = False

        if self.everything is None:
            should_auto_ignore = True
        
        self.everything = everything

        if should_auto_ignore:
            self.auto_ignored()

    def auto_ignored(self):
        if tree.INIT.I_MAIN in self.spaces:
            self.ignored.add(tree.SETTINGS.I_MAIN)
        
        if tree.SETTINGS.I_MAIN in self.spaces:
            ...
        
        if not self.everything.is_group_chat:
            self.ignored.add(tree.SETTINGS.III_SHOULD_PIN)

    @classmethod
    def from_db(cls: type[Navigator], db: DbNavigator, everything: Optional[common.CommonEverything] = None) -> Navigator:
        return cls(
            trace=[states.from_encoded(state) for state in db.trace],
            back_trace=[states.from_encoded(state) for state in db.back_trace],
            ignored=[states.from_encoded(state) for state in db.ignored],
            everything=everything
        )
    
    def to_db(self) -> DbNavigator:
        return DbNavigator.from_runtime(self)