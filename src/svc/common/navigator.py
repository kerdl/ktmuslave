from dataclasses import dataclass
from .states import Init, Hub, Space


@dataclass
class Navigator:
    """
    ## Traces user's path between states
    So he can use `← Back` button
    """
    # so we know which trace to use
    space: Space

    # example of `init_trace`:
    #    [ Init.MAIN, Init.GROUP, Init.SCHEDULE_BROADCAST ]
    #          ^                             ^
    #     where started                current state

    init_trace: list[Init]
    hub_trace: list[Hub]

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
            case Space.INIT:
                del self.init_trace[-1]
            case Space.HUB:
                del self.hub_trace[-1]