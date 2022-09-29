import re


NONWORD       = re.compile(r"\W")
GROUP         = re.compile(r"(\d)([-]{0,1})([а-яёА-ЯЁ]{3})([-]{0,1})(\d{2})")
NAME          = re.compile(r"[А-ЯЁ][а-яё]{1,}")
SPACE_NEWLINE = re.compile(r"\n\s{1,}\n")