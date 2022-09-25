import re


NONWORD = re.compile(r"\W")
GROUP   = re.compile(r"(\d)([-]{0,1})([а-яёА-ЯЁ]{3})([-]{0,1})(\d{2})")