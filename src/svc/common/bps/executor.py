import re
from src.svc.common import CommonEverything


EXECUTOR_TEMPLATE = """
async def __ex(everything):
    from src import defs

    _logs = ""
    _error = None

    def log(*args):
        nonlocal _logs

        str_args = [str(arg) for arg in args]

        joined_args = \" \".join(str_args)
        _logs += joined_args
        _logs += \"\\n\"
    
    try:
{code}
    except Exception as e:
        _error = e

    return (_logs, _error)
"""

async def execute(everything: CommonEverything, code: str) -> tuple[str, Exception]:
    code = code.replace(u"\u00a0", " ")

    wrapped_code = EXECUTOR_TEMPLATE.format(
        code="".join(f"\n        {l}" for l in code.split("\n"))
    )

    try:
        exec(
            wrapped_code,
            globals(),
            locals()
        )
    except Exception as e:
        return ("", e)

    return await locals()["__ex"](everything)