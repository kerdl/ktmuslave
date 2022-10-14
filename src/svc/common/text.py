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