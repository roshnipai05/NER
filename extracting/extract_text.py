import os
import pdfplumber
from tqdm import tqdm

PDF_DIR = "data/raw_pdfs"
TEXT_DIR = "data/raw_text"

os.makedirs(TEXT_DIR, exist_ok=True)

def extract_pdf_text(pdf_path):
    text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:

                page_text = ""
                chars = page.chars

                i = 0
                while i < len(chars):
                    char = chars[i]
                    fontname = char.get("fontname", "")
                    ch = char.get("text", "")

                    # Detect italic via font name
                    is_italic = "Italic" in fontname or "Oblique" in fontname

                    # Case 1: If normal text → keep
                    if not is_italic:
                        page_text += ch
                        i += 1
                        continue

                    # Case 2: If italic inside parentheses → remove whole bracket block
                    # Check if immediately preceded by "("
                    if i > 0 and chars[i - 1].get("text") == "(":
                        # Remove already-added "("
                        if page_text.endswith("("):
                            page_text = page_text[:-1]

                        # Skip until matching ")"
                        while i < len(chars) and chars[i].get("text") != ")":
                            i += 1

                        # Skip the closing ")"
                        i += 1
                        continue

                    # Case 3: Italic without parentheses → just skip
                    i += 1

                text += page_text + "\n"

    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return text
