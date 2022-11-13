CMD = "cmd"

def payload_eq(received: dict[str], to_compare: str) -> bool:
    return received == { CMD: to_compare }