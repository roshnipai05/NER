# V1/gazetteer.py

import json
import re


def load_party_gazetteer(path="data/party.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_party_entities(text, gazetteer):
    entities = []

    for full_name, acronyms in gazetteer.items():
        # Exact match full name
        for match in re.finditer(rf'\b{re.escape(full_name)}\b', text):
            entities.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "PARTY"
            })

        # Acronyms
        for acronym in acronyms:
            for match in re.finditer(rf'\b{re.escape(acronym)}\b', text):
                entities.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "label": "PARTY"
                })

    return entities
