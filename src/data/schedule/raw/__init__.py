from typing import Literal


class Type:
    FT_WEEKLY = "ft_weekly"
    FT_DAILY  = "ft_daily"
    R_WEEKLY  = "r_weekly"
    TCHR_FT_WEEKLY = "tchr_ft_weekly"
    TCHR_FT_DAILY  = "tchr_ft_daily"
    TCHR_R_WEEKLY  = "tchr_r_weekly"

TYPE_LITERAL = Literal[
    "ft_weekly",
    "ft_daily",
    "r_weekly",
    "tchr_ft_weekly",
    "tchr_ft_daily",
    "tchr_r_weekly"
]
