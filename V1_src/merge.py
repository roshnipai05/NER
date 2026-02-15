# V1/merge.py

def merge_entities(bert_entities, rule_entities):
    """
    Rule-based entities override BERT entities on overlap.
    """

    final_entities = []

    # First add rule entities (higher priority)
    final_entities.extend(rule_entities)

    for bert_ent in bert_entities:
        overlap = False
        for rule_ent in rule_entities:
            if not (bert_ent["end"] <= rule_ent["start"] or
                    bert_ent["start"] >= rule_ent["end"]):
                overlap = True
                break

        if not overlap:
            final_entities.append(bert_ent)

    return sorted(final_entities, key=lambda x: x["start"])
