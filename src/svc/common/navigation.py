from transitions import Machine

class State:
    class Init:
        ...

    class Hub:
        ...

    INIT = Init()
    HUB = Hub()

class Navigation:
    states = ["init", "hub"]

    def __init__(self):
        self.machine = Machine(
            model=self, 
            states=Navigation.states, 
            initial=State.HUB
        )

        self.machine.add_transition()