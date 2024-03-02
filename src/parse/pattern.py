import re


GROUP               = re.compile(r"([0-9])([-]{0,1})([а-яёА-ЯЁ]{3})([-]{0,1})([0-9]{1,2})")
NAME                = re.compile(r"[А-ЯЁ][а-яё]{1,}")
SHORT_NAME          = re.compile(r"([А-ЯЁ][а-яё]{1,})(\s)([А-ЯЁ]{1}[.])([А-ЯЁ]{1}[.]{0,1}){0,1}")
SPACE               = re.compile(r"\s")
SPACE_NEWLINE       = re.compile(r"\n\s{1,}\n")
DIGIT               = re.compile(r"\d")
NUMBER              = re.compile(r"\d{1,}")
LETTER              = re.compile(r"[^\W\d]")
NON_LETTER          = re.compile(r"\W")
NON_LETTER_NO_SPACE = re.compile(r"[^\w\s]")
PUNCTUATION         = re.compile(r"[!\"#\$%&\'\(\)\*\+,-\./:;<=>\?@\[\\\]\^_`{\|}~]")
ZOOM_ID             = re.compile(r"(\d{11}|\d{10})")
ZOOM_PWD            = re.compile(r"[A-Za-z0-9]{5,6}")
