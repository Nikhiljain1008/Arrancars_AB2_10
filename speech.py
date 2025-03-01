import speech_recognition as sr
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer, EmailRecognizer, PhoneRecognizer

# Initialize Presidio Analyzer
analyzer = AnalyzerEngine()

# Function to detect PII in text
def detect_pii(text):
    results = analyzer.analyze(text=text, language="en")
    
    if results:
        print("\n⚠️ PII Detected! Sensitive Information Found:")
        for r in results:
            print(f"🔴 Entity: {r.entity_type}, Text: {text[r.start:r.end]}")
        return True
    return False

# Real-time Transcription with PII Detection
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
                
                # Check for PII in real-time
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
