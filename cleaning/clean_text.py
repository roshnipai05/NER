import os
import re
from tqdm import tqdm

# Get absolute path of project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw_text")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned_text")

os.makedirs(CLEAN_DIR, exist_ok=True)



def remove_page_headers(text):
    # remove page markers like "23.03.2020 47"
    text = re.sub(r"\d{2}\.\d{2}\.\d{4} \d+", "", text)
    return text


def remove_timestamps(text):
    # remove time stamps like "14.05 hrs"
    text = re.sub(r"\d{1,2}\.\d{2}\s*½?\s*hrs", "", text)
    return text


def remove_bracketed_text(text):
    # remove [Translation], [English], etc.
    text = re.sub(r"\[.*?\]", "", text)
    return text


def remove_decorative_lines(text):
    text = re.sub(r"_+", "", text)
    return text


def remove_procedural_clauses(text):
    # remove Clause X blocks
    text = re.sub(r"Clause \d+.*?(?=Clause|\Z)", "", text, flags=re.DOTALL)
    return text


def clean_text(text):
    text = remove_page_headers(text)
    text = remove_timestamps(text)
    text = remove_bracketed_text(text)
    text = remove_decorative_lines(text)
    text = remove_procedural_clauses(text)

    # normalize whitespace
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


if __name__ == "__main__":
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".txt")]

    for file in tqdm(files):
        with open(os.path.join(RAW_DIR, file), "r", encoding="utf-8") as f:
            text = f.read()

        cleaned = clean_text(text)

        with open(os.path.join(CLEAN_DIR, file), "w", encoding="utf-8") as f:
            f.write(cleaned)

    print("Cleaning complete.")
