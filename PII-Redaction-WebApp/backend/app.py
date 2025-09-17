
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import cv2
import numpy as np
import io
from utils.pii_detector import detect_pii
import speech_recognition as sr
import re
from presidio_analyzer import AnalyzerEngine
import winsound
from datetime import datetime

app = Flask(__name__)
CORS(app)  


socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Socket error handling
@socketio.on_error()
def error_handler(e):
    print('SocketIO Error:', str(e))
    socketio.emit('error', {'message': str(e)})

@socketio.on('connect')
def handle_connect():
    print('👤 Client connected')
    socketio.emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('👤 Client disconnected')


POPPLER_PATH = (
    r"C:\Users\babusha kolhe\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
)


REDACTED_FOLDER = "redacted_documents"
os.makedirs(REDACTED_FOLDER, exist_ok=True)


analyzer = AnalyzerEngine()

def play_alert_sound():
    frequency = 1000  
    duration = 500  
    winsound.Beep(frequency, duration)  



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


def detect_pii_audio(text):
    detected_pii = []
    
    
    results = analyzer.analyze(text=text, language="en")

    
    for r in results:
        detected_pii.append((r.entity_type, text[r.start:r.end]))

    
    for category, pattern in PII_CATEGORIES.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            detected_pii.append((category, match.group()))

    if detected_pii:
        print("\n⚠️ PII Detected! Sensitive Information Found:")
        for entity, value in detected_pii:
            print(f"🔴 Entity: {entity}, Text: {value}")
        
        play_alert_sound()  
        return True

    return False
    


def detect_context(text):
    for pii_type, phrases in CONTEXT_REFERENCES.items():
        for phrase in phrases:
            if phrase.lower() in text.lower():
                print(f"⚠️ Potential PII Context Detected: {pii_type}")
                play_alert_sound()
                return pii_type  
    return None


def preprocess_image(image):
    """
    Preprocess the image to improve OCR accuracy.
    """
    
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresholded)


def redact_text(text, detected_pii):
    """
    Redact sensitive information in the text.
    """
    for pii_type, values in detected_pii.items():
        for value in values:
            text = text.replace(value, "[REDACTED]")
    return text


def mask_image(image, detected_pii, redaction_level):
    """
    Mask sensitive information in the image based on the selected redaction level.
    """
    from utils.pii_detector import PII_LEVEL_MAPPING

    
    levels_order = ['basic', 'intermediate', 'critical']

    
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    
    custom_config = r"--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, config=custom_config
    )
    print(data)
    
    for i in range(len(data["text"])):
        text = data["text"][i].strip()  
        if text:  
            for pii_type, values in detected_pii.items():
                
                if PII_LEVEL_MAPPING.get(pii_type, "basic") in levels_order[: levels_order.index(redaction_level) + 1]:
                    for value in values:
                        
                        if value.strip() in text:
                            
                            x, y, w, h = (
                                data["left"][i],
                                data["top"][i],
                                data["width"][i],
                                data["height"][i],
                            )
                            
                            cv2.rectangle(
                                image_cv, (x, y), (x + w, y + h), (0, 0, 0), -1
                            )  

    return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))


@app.route("/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    
    redaction_level = request.form.get("redaction_level", "basic").lower()
    levels_order = ["basic", "intermediate", "critical"]
    if redaction_level not in levels_order:
        redaction_level = "basic"  

    
    file_bytes = file.read()

    
    if file.filename.lower().endswith(".pdf"):
        
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
        text = ""
        all_detected_pii = {}  
        redacted_images = []

        for image in images:
            
            processed_image = preprocess_image(image)
            
            custom_config = r"--oem 3 --psm 6"
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
            text += extracted_text + "\n"

            print("Extracted Text from Page:", extracted_text)
            detected_pii = detect_pii(extracted_text)

            
            for pii_type, values in detected_pii.items():
                if pii_type in all_detected_pii:
                    all_detected_pii[pii_type].extend(v for v in values if v not in all_detected_pii[pii_type])
                else:
                    all_detected_pii[pii_type] = values.copy()

        
        from utils.pii_detector import PII_LEVEL_MAPPING
        filtered_pii = {
            pii_type: values
            for pii_type, values in all_detected_pii.items()
            if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
        }

        
        for image in images:
            masked_image = mask_image(image, filtered_pii, redaction_level)  
            redacted_images.append(masked_image)

        
        from fpdf import FPDF

        pdf = FPDF()
        for redacted_image in redacted_images:
            redacted_image_path = os.path.join(REDACTED_FOLDER, "temp.png")
            redacted_image.save(redacted_image_path)
            pdf.add_page()
            pdf.image(redacted_image_path, x=10, y=10, w=190)
            os.remove(redacted_image_path)  
        redacted_pdf_path = os.path.join(REDACTED_FOLDER, "redacted_document.pdf")
        pdf.output(redacted_pdf_path)
        redacted_file_url = f"/download/{os.path.basename(redacted_pdf_path)}"

    else:
        
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            processed_image = preprocess_image(image)
            
            custom_config = r"--oem 3 --psm 6"
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
            text = extracted_text

            
            detected_pii = detect_pii(extracted_text)

            
            from utils.pii_detector import PII_LEVEL_MAPPING
            filtered_pii = {
                pii_type: values
                for pii_type, values in detected_pii.items()
                if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
            }

            
            masked_image = mask_image(image, filtered_pii, redaction_level)  
            redacted_image_path = os.path.join(REDACTED_FOLDER, "redacted_image.png")
            masked_image.save(redacted_image_path)
            redacted_file_url = f"/download/{os.path.basename(redacted_image_path)}"
        except Exception as e:
            return jsonify({"error": f"Cannot process file: {str(e)}"}), 400

    
    redacted_text = redact_text(text, filtered_pii)

    
    socketio.emit("pii_detected", {"detected_pii": filtered_pii})

    return jsonify(
        {
            "text": text,
            "redacted_text": redacted_text,
            "detected_pii": filtered_pii,
            "redacted_file_url": redacted_file_url,  
        }
    )

# Global variable to track transcription state
is_transcribing = False

@socketio.on("start_transcription")
def handle_transcription(data):
    global is_transcribing
    is_transcribing = True
    
    recognizer = sr.Recognizer()
    silence_counter = 0

    try:
        # Notify client that transcription is starting
        socketio.emit('transcription_status', {'status': 'starting'})
        
        with sr.Microphone() as source:
            print("🎤 Listening... Speak now!")
            socketio.emit('transcription_status', {'status': 'listening'})
            
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            print("🔊 Adjusted for ambient noise")

            while silence_counter < 6 and is_transcribing:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)

                    print("📝 Transcription:", text)

                    # Send transcription update to client
                    print(f"📤 Sending transcription_update -> {text}")
                    socketio.emit("transcription_update", {
                        "text": text,
                        "timestamp": str(datetime.now())
                    })

                    # Check for PII in context
                    context_pii = detect_context(text)
                    if context_pii:
                        print(f"📤 Sending pii_alert (context) -> {context_pii}")
                        socketio.emit("pii_alert", {
                            "type": context_pii,
                            "value": text,
                            "source": "context",
                            "timestamp": str(datetime.now())
                        })

                    # Check for PII in content
                    if detect_pii_audio(text):
                        print(f"📤 Sending pii_alert (content) -> PII detected")
                        socketio.emit("pii_alert", {
                            "type": "PII",
                            "value": text,
                            "source": "content",
                            "timestamp": str(datetime.now())
                        })

                    silence_counter = 0

                except sr.WaitTimeoutError:
                    print("⏳ No speech detected, still listening...")
                    socketio.emit('transcription_status', {'status': 'waiting'})
                    silence_counter += 1
                except sr.UnknownValueError:
                    print("❌ Could not understand the audio")
                    socketio.emit('transcription_status', {'status': 'unclear'})
                except sr.RequestError as e:
                    print("❌ API unavailable:", str(e))
                    socketio.emit('error', {'message': 'Speech recognition service unavailable'})
                    break

        print("🔴 Transcription stopped")
        socketio.emit("transcription_complete", {
            "status": "done",
            "reason": "timeout" if silence_counter >= 6 else "stopped"
        })
    
    except Exception as e:
        print("❌ Error in transcription:", str(e))
        socketio.emit('error', {'message': str(e)})
    
    finally:
        is_transcribing = False

@socketio.on("stop_transcription")
def handle_stop_transcription():
    global is_transcribing
    print("🛑 Stop transcription requested")
    is_transcribing = False
    socketio.emit('transcription_status', {'status': 'stopped'})

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(REDACTED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)  