from dataclasses import dataclass
from typing import Literal
from .states.tree import Init, Hub, Space


@dataclass
class Navigator:
    """
    ## Traces user's path between states
    So he can use `← Back` button
    """

    # example of `init_trace`:
    #    [ Init.MAIN, Init.GROUP, Init.SCHEDULE_BROADCAST ]
    #          ^                             ^
    #     where started                current state

    init_trace: list[Init]
    hub_trace: list[Hub]

    # so we know which trace to use
    space: Literal["init", "hub"] = Space.INIT

    @property
    def current_init(self) -> Init:
        """
        ## Last state from `init_trace`
        """
        return self.init_trace[-1]
    
    @property
    def current_hub(self) -> Hub:
        """
        ## Last state from `hub_trace`
        """
        return self.hub_trace[-1]

    def back(self):
        """
        ## Remove last state from current space
        """
        match self.space:
            case Space.INIT if self.init_trace > 0:
                del self.init_trace[-1]
            case Space.HUB if self.hub_trace > 0:
                del self.hub_trace[-1]