import datetime
from typing import Optional
from src.data.range import Range


def current() -> Range[datetime.date]:
    today = datetime.date.today()
    # Today - Current weekday number = Monday
    start = today - datetime.timedelta(days=today.weekday())
    # Monday + 7 = Monday
    # (since Range is non-inclusive, it includes Sunday but not Monday)
    end = start + datetime.timedelta(days=7)
    return Range(start=start, end=end)
    
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
    
    # Monday + 7 = Monday
    # (since Range is non-inclusive, it includes Sunday but not Monday)
    end = start + datetime.timedelta(days=7)
    return Range(start=start, end=end)

def from_day(day: datetime.date) -> Range[datetime.date]:
    """
    # Get the week of `day`
    """
    start = day - datetime.timedelta(days=day.weekday())
    end = start + datetime.timedelta(days=7)
    return Range(start=start, end=end)

def index_day(rng: Range[datetime.date], idx: int) -> Optional[datetime.date]:
    return rng.start + datetime.timedelta(days=idx)

def previous(rng: Range[datetime.date]) -> Range[datetime.date]:
    """
    # Get previous week
    """
    start = rng.start - datetime.timedelta(days=7)
    end = rng.end - datetime.timedelta(days=7)
    return Range(start=start, end=end)

def next(rng: Range[datetime.date]) -> Range[datetime.date]:
    """
    # Get next week
    """
    start = rng.start + datetime.timedelta(days=7)
    end = rng.end + datetime.timedelta(days=7)
    return Range(start=start, end=end)

def ensure_next_after_current(rng: Range[datetime.date]) -> Range[datetime.date]:
    return starting_from_day(index_day(current(), rng.start.weekday()))

def starting_from_day(day: datetime.date) -> Range[datetime.date]:
    """
    # A week starting from `day`
    """
    end = day + datetime.timedelta(days=7)
    return Range(start=day, end=end)

def cover_today(idx: int) -> Range[datetime.date]:
    """
    # Make a range covering today's weekday, starting from `idx`
    """
    today = datetime.date.today()
    
    if today.weekday() == idx:
        # start the week from today
        return starting_from_day(today)
    else:
        # start from previous week
        curr = from_day(today)
        prev = previous(curr)
        prev_weekday = prev.start + datetime.timedelta(days=idx)
        return starting_from_day(prev_weekday)
