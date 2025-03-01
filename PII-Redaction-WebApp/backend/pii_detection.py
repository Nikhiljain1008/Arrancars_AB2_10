import re
import spacy
nlp = spacy.load("en_core_web_sm")
# Define common PII regex patterns
PII_LEVELS = {
    "basic": ["email", "phone"],
    "sensitive": ["email", "phone", "SSN", "credit_card"],
    "critical": ["email", "phone", "SSN", "credit_card", "PERSON", "GPE"]  # Includes names & addresses
}

# def detect_pii_and_redact(text):
#     """Detect and redact multiple types of PII in the given text."""
#     detected = {}
#     redacted_text = text

#     # Email Redaction
#     email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
#     if re.search(email_pattern, text):
#         detected["email"] = "Detected"
#         redacted_text = re.sub(email_pattern, "[REDACTED_EMAIL]", redacted_text)

#     # Phone Number Redaction (US format)
#     phone_pattern = r"\b\d{3}-\d{3}-\d{4}\b"
#     if re.search(phone_pattern, text):
#         detected["phone"] = "Detected"
#         redacted_text = re.sub(phone_pattern, "[REDACTED_PHONE]", redacted_text)

#     # SSN Redaction (US)
#     ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
#     if re.search(ssn_pattern, text):
#         detected["SSN"] = "Detected"
#         redacted_text = re.sub(ssn_pattern, "[REDACTED_SSN]", redacted_text)

#     # Credit Card Number Redaction (Visa, Mastercard, Amex)
#     credit_card_pattern = r"\b(?:\d[ -]*?){13,16}\b"
#     if re.search(credit_card_pattern, text):
#         detected["credit_card"] = "Detected"
#         redacted_text = re.sub(credit_card_pattern, "[REDACTED_CARD]", redacted_text)

#     # Apply spaCy NER for detecting names and addresses
#     doc = nlp(text)
#     for ent in doc.ents:
#         if ent.label_ in ["PERSON", "GPE", "ORG", "LOC"]:  # Detect Names and Addresses
#             detected[ent.label_] = "Detected"
#             redacted_text = redacted_text.replace(ent.text, f"[REDACTED_{ent.label_}]")

#     return {"detected_pii": detected, "redacted_text": redacted_text}\
def detect_pii_and_redact(text, pii_level="critical"):
    """Detect and redact multiple types of PII based on the selected level."""
    detected = {}
    redacted_text = text

    # Ensure level is valid
    pii_types = PII_LEVELS.get(pii_level.lower(), PII_LEVELS["critical"])

    # Patterns for PII
    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}-\d{3}-\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b"
    }

    # Regex-based PII detection
    for pii, pattern in patterns.items():
        if pii in pii_types and re.search(pattern, text):
            detected[pii] = "Detected"
            redacted_text = re.sub(pattern, f"[REDACTED_{pii.upper()}]", redacted_text)

    # NER-based detection (for critical level)
    if "PERSON" in pii_types or "GPE" in pii_types:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in pii_types:
                detected[ent.label_] = "Detected"
                redacted_text = redacted_text.replace(ent.text, f"[REDACTED_{ent.label_}]")

    return {"detected_pii": detected, "redacted_text": redacted_text}