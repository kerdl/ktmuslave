from typing import Literal


class Type:
    FT_WEEKLY = "ft_weekly"
    FT_DAILY  = "ft_daily"
    R_WEEKLY  = "r_weekly"

TYPE_LITERAL = Literal["ft_weekly", "ft_daily", "r_weekly"]