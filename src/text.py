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

def shorten_lines(text: str, limit: int = 4000) -> list[str]:
    newline_split = text.split("\n")
    shortened_lines = []

    for line in newline_split:
        while len(line) > limit:
            short = line[:limit]
            line = line.removeprefix(short)
            shortened_lines.append(short)
        else:
            shortened_lines.append(line)
    
    return shortened_lines

def chunks_len(chunks: list[str]) -> int:
    length = 0

    for chunk in chunks:
        length += len(chunk)
    
    return length

def chunks(text: str, limit: int = 4000) -> list[str]:
    shortened_lines = shorten_lines(text, limit)
    output: list[str] = []

    lines: list[str] = []
    for (index, line) in enumerate(shortened_lines):
        is_last = (index + 1) == len(shortened_lines)

        if chunks_len(lines) > limit:
            last_line = lines[-1]
            del lines[-1]

            output.append("\n".join(lines))
            lines = []
            lines.append(last_line)
            lines.append(line)
        
        elif is_last:
            lines.append(line)
            output.append("\n".join(lines))
        
        else:
            lines.append(line)
    
    return output

def double_newline_chunks(text: str, limit: int = 4000) -> list[str]:
    blocks = text.split("\n\n")
    output: list[str] = []

    temp_blocks: list[str] = []
    for block in blocks:
        temps_len = chunks_len(temp_blocks)

        if (temps_len + len(block)) > limit:
            output.append("\n\n".join(temp_blocks))
            temp_blocks = []
            temp_blocks.append(block)
        else:
            temp_blocks.append(block)

    output.append("\n\n".join(temp_blocks))
    
    return output