def indent(
    text: str, 
    width: int = 3, 
    times: int = 1, 
    add_dropdown: bool = False
):
    """
    # Indent text, even multilines
    """

    indentation = (" " * width) * times

    lines: list[str] = []

    for line in text.split("\n"):
        already_dropdowned = False

        if line.startswith(" ") and "╰" in line:
            # this line is indented
            # and dropped down, 
            # avoid adding one more dropdown
            already_dropdowned = True

        if add_dropdown and not already_dropdowned:
            dropdown_line = f"╰ {line}"
        elif already_dropdowned:
            dropdown_line = f" {line}"
        else:
            dropdown_line = line

        indented_line = indentation + dropdown_line
    
        lines.append(indented_line)
    
    return "\n".join(lines)

def shorten(text: str, limit: int = 10) -> str:
    text = str(text)

    if len(text) > limit:
        text = text[:limit] + "..."
    
    return text