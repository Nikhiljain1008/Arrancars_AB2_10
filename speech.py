import speech_recognition as sr
import re
from presidio_analyzer import AnalyzerEngine, RecognizerResult
import winsound

def play_alert_sound():
    frequency = 1000  # Set frequency to 1000 Hz
    duration = 500  # Set duration to 500 milliseconds
    winsound.Beep(frequency, duration)  # Play sound

# Initialize Presidio Analyzer
analyzer = AnalyzerEngine()

# Context References: Phrases that indicate upcoming PII
CONTEXT_REFERENCES = {
    "CREDIT_CARD_NUMBER": [
        "my credit card number is", 
        "here is my credit card", 
        "this is my card number", 
        "use this card for payment",
        "enter my credit card details"
    ],
    "DEBIT_CARD_NUMBER": [
        "my debit card number is", 
        "here is my debit card", 
        "this is my ATM card number", 
        "use this for the transaction"
    ],
    "AADHAAR_NUMBER": [
        "my Aadhaar number is", 
        "Aadhaar number is", 
        "this is my UIDAI number", 
        "provide my Aadhaar"
    ],
    "PAN_NUMBER": [
        "my PAN number is", 
        "here is my PAN", 
        "this is my tax ID"
    ],
    "PASSPORT_NUMBER": [
        "my passport number is", 
        "passport details are", 
        "this is my travel document number"
    ],
    "DRIVING_LICENSE": [
        "my driving license number is", 
        "license details are", 
        "this is my DL number"
    ],
    "BANK_ACCOUNT_NUMBER": [
        "my bank account number is", 
        "account number is", 
        "deposit it in this account",
        "transfer money to this account"
    ],
    "IFSC_CODE": [
        "the IFSC code is", 
        "use this bank IFSC", 
        "branch IFSC is"
    ],
    "UPI_ID": [
        "send money to this UPI", 
        "my UPI ID is", 
        "pay me at this UPI handle"
    ],
    "PHONE_NUMBER": [
        "my phone number is", 
        "here is my contact number", 
        "call me at this number"
    ],
    "EMAIL_ADDRESS": [
        "my email address is", 
        "send it to my email", 
        "contact me at this email"
    ]
}


# Custom PII Categories with Regular Expressions
PII_CATEGORIES = {
    "AADHAAR_NUMBER": r"\b\d{4}\s\d{4}\s\d{4}\b",
    "PAN_NUMBER": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "PASSPORT_NUMBER": r"\b[A-Z]{1}[0-9]{7}\b",
    "DRIVING_LICENSE": r"\b[A-Z]{2}\d{2}\s\d{4}\s\d{7}\b",
    "CREDIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "DEBIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "BANK_ACCOUNT_NUMBER": r"\b\d{9,18}\b",
    "IFSC_CODE": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "UPI_ID": r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b",
    "PHONE_NUMBER": r"\b\d{10}\b",
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
}


# Function to detect PII in text
def detect_pii(text):
    detected_pii = []
    
    # Use Presidio for built-in PII detection
    results = analyzer.analyze(text=text, language="en")

    # Collect detected entities from Presidio
    for r in results:
        detected_pii.append((r.entity_type, text[r.start:r.end]))

    # Use regex to detect additional PII
    for category, pattern in PII_CATEGORIES.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            detected_pii.append((category, match.group()))

    # If PII is found, play alert sound
    if detected_pii:
        print("\n⚠️ PII Detected! Sensitive Information Found:")
        for entity, value in detected_pii:
            print(f"🔴 Entity: {entity}, Text: {value}")
        
        play_alert_sound()  # Play buzzer when PII is detected
        return True

    return False

# Function to detect context-based PII hints
def detect_context(text):
    for pii_type, phrases in CONTEXT_REFERENCES.items():
        for phrase in phrases:
            if phrase.lower() in text.lower():
                print(f"⚠️ Potential PII Context Detected: {pii_type}")
                play_alert_sound()
                return pii_type  # Return the type of PII being hinted
    return None

# Real-time Transcription with Context + Full PII Detection
def live_transcription():
    recognizer = sr.Recognizer()
    silence_counter = 0  # Stop after 30 sec of silence
    
    with sr.Microphone() as source:
        print("🎤 Listening... Speak now!")
        recognizer.adjust_for_ambient_noise(source)  

        while silence_counter < 6:  # Stop after 6 silent periods (30 sec)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                
                print("📝 Transcription:", text)
                
                # Step 1: Detect context-based hints (Proactive)
                context_pii = detect_context(text)
                if context_pii:
                    print(f"⚠️ ALERT: User is about to provide {context_pii}!")

                # Step 2: Detect actual PII (Reactive)
                if detect_pii(text):
                    print("⚠️ ALERT: PII detected in speech! Take necessary actions.")

                silence_counter = 0  # Reset silence counter if speech is detected
            
            except sr.WaitTimeoutError:
                print("⏳ No speech detected, still listening...")
                silence_counter += 1
            except sr.UnknownValueError:
                print("❌ Could not understand the audio")
            except sr.RequestError:
                print("❌ API unavailable")

        print("🔴 No speech detected for too long. Stopping.")

# Run the real-time PII detection system
live_transcription()
