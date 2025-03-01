"""
PII Detection Using Regex & NER
"""
import re
import spacy

nlp = spacy.load("en_core_web_sm")

# Regex patterns for common PII
def detect_pii(text):
    patterns = {
        "Aadhaar": r"\b\d{4} \d{4} \d{4}\b",
        "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        "Phone": r"\b\d{10}\b"
    }
    matches = {key: re.findall(pattern, text) for key, pattern in patterns.items()}
    return matches
