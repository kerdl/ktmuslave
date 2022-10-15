def indent(text: str, width: int = 3, times: int = 1):
    """
    # Indent text, even multilines
    """

    indentation = (" " * width) * times

    lines: list[str] = []

    for line in text.split("\n"):
        indented_line = indentation + line
        lines.append(indented_line)
    
    return "\n".join(lines)

def shorten(text: str, limit: int = 10) -> str:
    text = str(text)

    if len(text) > limit:
        text = text[:limit] + "..."
    
    return text