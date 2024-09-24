import datetime
from src.data.range import Range


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
    
    # Monday + 6 = Sunday
    end = start + datetime.timedelta(days=6)
    return Range(start=start, end=end)