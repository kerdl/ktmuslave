import datetime
from src.data.range import Range


def eq_with_now(other: Range[datetime.date]) -> bool:
    now = current_active()
    return now == other
    
def current_active() -> Range[datetime.date]:
    """
    # Get current active week
    ## Returns
    - current week if today's Monday - Saturday
    - next week if today's Sunday
    """
    today = datetime.date.today()
    
    # 6 == Sunday
    if today.weekday() == 6:
        # Sunday + 1 = Monday
        start = today + datetime.timedelta(days=1) 
    else:
        # Today - Current weekday number = Monday
        start = today - datetime.timedelta(days=today.weekday())
    
    # Monday + 7 = Monday, but since Range is non-inclusive, it is Sunday
    end = start + datetime.timedelta(days=7)
    return Range(start=start, end=end)

def from_day(day: datetime.date) -> Range[datetime.date]:
    """
    # Get the week of `day`
    """
    start = day - datetime.timedelta(days=day.weekday())
    end = start + datetime.timedelta(days=7)
    return Range(start=start, end=end)

def shift_backwards(rng: Range[datetime.date]) -> Range[datetime.date]:
    """
    # Get previous week from provided
    
    ## Exceptions
    Throws `ValueError` if `rng`
    does not start from Monday and
    does not end with Sunday
    """
    if rng.start.weekday() != 0:
        raise ValueError("rng does not start with Monday")
    if rng.end.weekday() != 0:
        raise ValueError("rng does not end with Sunday")

    prev_sunday = rng.start - datetime.timedelta(days=1)
    prev_monday = prev_sunday - datetime.timedelta(days=7)
    return Range(start=prev_monday, end=prev_sunday)
    
def shift_forward(rng: Range[datetime.date]) -> Range[datetime.date]:
    """
    # Get next week from provided
    
    ## Exceptions
    Throws `ValueError` if `rng`
    does not start from Monday and
    does not end with Sunday
    """
    if rng.start.weekday() != 0:
        raise ValueError("rng does not start with Monday")
    if rng.end.weekday() != 0:
        raise ValueError("rng does not end with Sunday")
    
    next_monday = rng.end + datetime.timedelta(days=1)
    next_sunday = next_monday + datetime.timedelta(days=7)
    return Range(start=next_monday, end=next_sunday)