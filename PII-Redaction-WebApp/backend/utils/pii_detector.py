import re
import spacy

# Load SpaCy's English language model
nlp = spacy.load("en_core_web_sm")

# Define regex patterns for PII detection
PII_PATTERNS = {
    "aadhaar": r"(?<!\d)(\d{4}\s\d{4}\s\d{4})(?!\s\d{4})",  # Aadhaar Number
    "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",  # PAN Number
    "voter_id": r"\b[A-Z]{3}[0-9]{7}\b",  # Voter ID
    "driving_license": r"\b[A-Z]{2}\d{2}\s\d{4}\s\d{7}\b",  # Driving License
    "passport": r"\b[A-Z]{1}[0-9]{7}\b",  # Passport Number
    "credit_card": r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
    "debit_card": r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",  # Debit Card Number
    "bank_account": r"\b\d{9,18}\b",  # Bank Account Number
    "ifsc": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",  # IFSC Code
    "upi_id": r"\b[a-zA-Z0-9.\-_]{2,}@(upi|ybl|paytm|okhdfcbank|okicici|oksbi|okaxis|okpayzapp|upiid)\b",
    "phone": r"\b[6789]\d{9}\b",  # Indian Phone Number
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "pincode": r"\b\d{6}\b",  # Indian PIN Code
    "gst": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b",  # GST Number
    "cin": r"\b[LU]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b",  # Corporate Identification Number
    "esic": r"\b\d{2}-\d{3}-\d{6}-\d\b",  # ESIC Number
    "pf": r"\b[A-Z]{2}/\d{5}/\d{7}\b",  # Provident Fund Number
    "social_security": r"\b[A-Z]{2}\d{6}[A-Z]{1}\b",  # Indian Social Security Number
    "tin": r"\b\d{11}\b",  # Taxpayer Identification Number
    "vehicle_registration": r"\b[A-Z]{2}-\d{2}-[A-Z]{1,2}-\d{4}\b",  # Vehicle Registration Number
    "dob": r"\b\d{2}[-/]\d{2}[-/]\d{4}\b",  # Date of Birth (DD-MM-YYYY or similar)
}

# Contextual keywords for each PII type
CONTEXTUAL_KEYWORDS = {
    "aadhaar": ["aadhaar", "uid", "unique identification"],
    "pan": ["pan", "permanent account number"],
    "voter_id": ["voter id", "voter card", "election card"],
    "driving_license": ["driving license", "dl no", "driver license"],
    "passport": ["passport", "passport no"],
    "credit_card": ["credit card", "cc no"],
    "debit_card": ["debit card", "dc no"],
    "bank_account": ["bank account", "account no", "acc no"],
    "ifsc": ["ifsc", "ifsc code"],
    "upi_id": ["upi", "upi id"],
    "phone": ["phone", "mobile", "contact no"],
    "email": ["email", "e-mail"],
    "pincode": ["pincode", "pin code", "postal code"],
    "gst": ["gst", "gstin"],
    "cin": ["cin", "corporate identification number"],
    "esic": ["esic", "employee state insurance"],
    "pf": ["pf", "provident fund"],
    "social_security": ["social security", "ssn"],
    "tin": ["tin", "taxpayer identification number"],
    "vehicle_registration": ["vehicle registration", "rc no"],
    "dob": ["dob", "date of birth", "birth date"],
}


def detect_with_context(text, pii_type):
    """
    Detect PII using contextual keywords.
    """
    detected_pii = []
    for keyword in CONTEXTUAL_KEYWORDS[pii_type]:
        # Look for the keyword followed by the PII pattern
        pattern = rf"{keyword}[:\s]*({PII_PATTERNS[pii_type]})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            detected_pii.extend(matches)
    return detected_pii


def detect_pii(text):
    """
    Detect PII in the given text using regex, contextual rules, and SpaCy.
    """
    detected_pii = {}

    # Detect PII using regex and contextual rules
    for pii_type in PII_PATTERNS:
        # Detect using regex
        regex_matches = re.findall(PII_PATTERNS[pii_type], text)
        # Detect using contextual rules
        contextual_matches = detect_with_context(text, pii_type)
        # Combine results
        matches = list(set(regex_matches + contextual_matches))  # Remove duplicates
        if matches:
            detected_pii[pii_type] = matches

    # Detect PII using SpaCy
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in [
            "PERSON",
            "DATE",
            "GPE",
        ]:  # PERSON = Name, DATE = Date, GPE = Location
            if ent.label_ not in detected_pii:
                detected_pii[ent.label_] = []
            detected_pii[ent.label_].append(ent.text)

    return detected_pii