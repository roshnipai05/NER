# V1/v1_pipeline.py

import os
import json
import pickle

from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

from regex_rules import find_regex_entities
from gazetteer import load_party_gazetteer, find_party_entities
from merge import merge_entities
from utils import convert_bert_output, tokenize_with_offsets, create_bio_labels


class V1NERPipeline:

    def __init__(self, party_path="data/party.json"):
        self.tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
        self.model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
        self.bert_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer)

        self.party_gazetteer = load_party_gazetteer(party_path)

    def process_text(self, text):

        # Run BERT
        bert_raw = self.bert_pipeline(text)
        bert_entities = convert_bert_output(bert_raw)

        # Regex entities
        regex_entities = find_regex_entities(text)

        # Gazetteer entities
        party_entities = find_party_entities(text, self.party_gazetteer)

        rule_entities = regex_entities + party_entities

        # Merge (rules override BERT)
        final_entities = merge_entities(bert_entities, rule_entities)

        # Token-level BIO
        tokens, offsets = tokenize_with_offsets(text)
        bio_labels = create_bio_labels(tokens, offsets, final_entities)

        return {
            "tokens": tokens,
            "bio_labels": bio_labels,
            "entities": final_entities
        }

    def process_json_file(self, json_path):

        with open(json_path, "r", encoding="utf-8") as f:
            debate_json = json.load(f)

        results = {}

        for speech in debate_json["speeches"]:
            speech_id = speech["speech_id"]
            text = speech["speech_text"]

            results[speech_id] = self.process_text(text)

        return results


def process_structured_folder(input_folder="data/structured_eval",
                              output_path="outputs/V1_predictions.pkl"):

    pipeline_obj = V1NERPipeline()

    all_results = {}

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):

            full_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            file_results = pipeline_obj.process_json_file(full_path)
            all_results.update(file_results)

    os.makedirs("outputs", exist_ok=True)

    with open(output_path, "wb") as f:
        pickle.dump(all_results, f)

    print("All files processed and saved.")


if __name__ == "__main__":
    process_structured_folder()
