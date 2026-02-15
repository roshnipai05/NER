# V1/utils.py

import re


def convert_bert_output(ner_results):
    """
    Convert HuggingFace pipeline output to clean span format.
    """
    entities = []

    for ent in ner_results:
        entities.append({
            "text": ent["word"],
            "start": ent["start"],
            "end": ent["end"],
            "label": ent["entity"].replace("B-", "").replace("I-", "")
        })

    return entities


def tokenize_with_offsets(text):
    tokens = []
    offsets = []

    for match in re.finditer(r'\S+', text):
        tokens.append(match.group())
        offsets.append((match.start(), match.end()))

    return tokens, offsets


def create_bio_labels(tokens, offsets, entities):
    labels = ["O"] * len(tokens)

    for ent in entities:
        ent_start = ent["start"]
        ent_end = ent["end"]
        ent_label = ent["label"]

        for i, (tok_start, tok_end) in enumerate(offsets):
            if tok_start >= ent_start and tok_end <= ent_end:
                if labels[i] == "O":
                    if tok_start == ent_start:
                        labels[i] = f"B-{ent_label}"
                    else:
                        labels[i] = f"I-{ent_label}"

    return labels
