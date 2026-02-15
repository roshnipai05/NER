# V1/regex_rules.py

import re

SCHEME_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z]*(?:\s[A-Z][A-Za-z]*)*)\s(Scheme|Yojana|Mission|Abhiyan|Campaign)\b'
)

BILL_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z\'()\-&,]*(?:\s[A-Z][A-Za-z\'()\-&,]*)*)\sBill\b'
)

ACT_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z\'()\-&,]*(?:\s[A-Z][A-Za-z\'()\-&,]*)*)\sAct\b'
)


def find_regex_entities(text):
    entities = []

    for pattern, label in [
        (SCHEME_PATTERN, "SCHEME"),
        (BILL_PATTERN, "BILL"),
        (ACT_PATTERN, "ACT")
    ]:
        for match in pattern.finditer(text):
            start, end = match.span()
            entities.append({
                "text": text[start:end],
                "start": start,
                "end": end,
                "label": label
            })

    return entities
