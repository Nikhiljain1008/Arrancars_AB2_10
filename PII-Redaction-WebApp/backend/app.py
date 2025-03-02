# # import os
# # from flask import Flask, request, jsonify, send_from_directory
# # from flask_cors import CORS
# # from flask_socketio import SocketIO, emit
# # import pytesseract
# # from pdf2image import convert_from_bytes
# # from PIL import Image
# # import cv2
# # import numpy as np
# # import io
# # from utils.pii_detector import detect_pii
# # from flask import Flask, request, jsonify
# # import speech_recognition as sr
# # import re
# # from presidio_analyzer import AnalyzerEngine
# # import winsound

# # app = Flask(__name__)
# # CORS(app)  # Enable CORS for all routes

# # # Initialize SocketIO without specifying async_mode
# # socketio = SocketIO(app, cors_allowed_origins="*")

# # # Set the Poppler path (update this to your Poppler bin directory)
# # POPPLER_PATH = (
# #     r"C:\Users\aadil\Desktop\poppler-24.08.0\Library\bin"
# # )

# # # Folder to store redacted documents
# # REDACTED_FOLDER = "redacted_documents"
# # os.makedirs(REDACTED_FOLDER, exist_ok=True)


# # def preprocess_image(image):
# #     """
# #     Preprocess the image to improve OCR accuracy.
# #     """
# #     # Convert to grayscale
# #     gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
# #     # Apply Gaussian blur
# #     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
# #     # Apply binary thresholding
# #     _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# #     return Image.fromarray(thresholded)


# # def redact_text(text, detected_pii):
# #     """
# #     Redact sensitive information in the text.
# #     """
# #     for pii_type, values in detected_pii.items():
# #         for value in values:
# #             text = text.replace(value, "[REDACTED]")
# #     return text


# # def mask_image(image, detected_pii, redaction_level):
# #     """
# #     Mask sensitive information in the image based on the selected redaction level.
# #     """
# #     from utils.pii_detector import PII_LEVEL_MAPPING

# #     # Define the order of redaction levels
# #     levels_order = ['basic', 'intermediate', 'critical']

# #     # Convert PIL image to OpenCV format
# #     image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# #     # Use Tesseract to detect text and their bounding boxes
# #     custom_config = r"--oem 3 --psm 6"
# #     data = pytesseract.image_to_data(
# #         image, output_type=pytesseract.Output.DICT, config=custom_config
# #     )

# #     # Log detected PII and redaction level
# #     print(f"Redaction Level: {redaction_level}")
# #     print(f"Detected PII: {detected_pii}")

# #     # Loop through detected text and mask PII
# #     for i in range(len(data["text"])):
# #         text = data["text"][i].strip()  # Remove leading/trailing whitespace
# #         if text:  # Only process non-empty text
# #             for pii_type, values in detected_pii.items():
# #                 # Check if the PII type matches the selected redaction level
# #                 if PII_LEVEL_MAPPING.get(pii_type, "basic") in levels_order[: levels_order.index(redaction_level) + 1]:
# #                     for value in values:
# #                         # Check if the detected text contains the PII value
# #                         if value.strip() in text:
# #                             # Log the PII being masked
# #                             print(f"Masking {pii_type}: {value}")

# #                             # Get the bounding box coordinates
# #                             x, y, w, h = (
# #                                 data["left"][i],
# #                                 data["top"][i],
# #                                 data["width"][i],
# #                                 data["height"][i],
# #                             )
# #                             # Mask the area
# #                             cv2.rectangle(
# #                                 image_cv, (x, y), (x + w, y + h), (0, 0, 0), -1
# #                             )  # Black out the area

# #     return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))


# # # Route for uploading and processing documents
# # @app.route("/upload", methods=["POST"])
# # def upload_document():
# #     if "file" not in request.files:
# #         return jsonify({"error": "No file uploaded"}), 400

# #     file = request.files["file"]
# #     if file.filename == "":
# #         return jsonify({"error": "No file selected"}), 400

# #     # Get the selected redaction level from the form data
# #     redaction_level = request.form.get("redaction_level", "basic").lower()
# #     levels_order = ["basic", "intermediate", "critical"]
# #     if redaction_level not in levels_order:
# #         redaction_level = "basic"  # Default to basic if invalid level is provided

# #     # Read the file into memory
# #     file_bytes = file.read()

# #     # Check if the file is a PDF
# #     if file.filename.lower().endswith(".pdf"):
# #         # Convert PDF to images
# #         images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
# #         text = ""
# #         all_detected_pii = {}  # Accumulate detected PII across all pages
# #         redacted_images = []

# #         for image in images:
# #             # Preprocess the image
# #             processed_image = preprocess_image(image)
# #             # Extract text using OCR
# #             custom_config = r"--oem 3 --psm 6"
# #             extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
# #             text += extracted_text + "\n"

# #             # Detect PII in the extracted text
# #             detected_pii = detect_pii(extracted_text)

# #             # Accumulate detected PII across all pages
# #             for pii_type, values in detected_pii.items():
# #                 if pii_type in all_detected_pii:
# #                     all_detected_pii[pii_type].extend(v for v in values if v not in all_detected_pii[pii_type])
# #                 else:
# #                     all_detected_pii[pii_type] = values.copy()

# #         # Filter detected PII based on the selected redaction level
# #         from utils.pii_detector import PII_LEVEL_MAPPING
# #         filtered_pii = {
# #             pii_type: values
# #             for pii_type, values in all_detected_pii.items()
# #             if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
# #         }

# #         # Log filtered PII
# #         print(f"Filtered PII for level {redaction_level}: {filtered_pii}")

# #         # Mask sensitive information in the images using filtered PII and redaction level
# #         for image in images:
# #             masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
# #             redacted_images.append(masked_image)

# #         # Save redacted images as a PDF
# #         from fpdf import FPDF

# #         pdf = FPDF()
# #         for redacted_image in redacted_images:
# #             redacted_image_path = os.path.join(REDACTED_FOLDER, "temp.png")
# #             redacted_image.save(redacted_image_path)
# #             pdf.add_page()
# #             pdf.image(redacted_image_path, x=10, y=10, w=190)
# #             os.remove(redacted_image_path)  # Clean up temporary files
# #         redacted_pdf_path = os.path.join(REDACTED_FOLDER, "redacted_document.pdf")
# #         pdf.output(redacted_pdf_path)
# #         redacted_file_url = f"/download/{os.path.basename(redacted_pdf_path)}"

# #     else:
# #         # Handle image files (JPEG, PNG, etc.)
# #         try:
# #             image = Image.open(io.BytesIO(file_bytes))
# #             # Preprocess the image
# #             processed_image = preprocess_image(image)
# #             # Extract text using OCR
# #             custom_config = r"--oem 3 --psm 6"
# #             extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
# #             text = extracted_text

# #             # Detect PII in the extracted text
# #             detected_pii = detect_pii(extracted_text)

# #             # Filter detected PII based on the selected redaction level
# #             from utils.pii_detector import PII_LEVEL_MAPPING
# #             filtered_pii = {
# #                 pii_type: values
# #                 for pii_type, values in detected_pii.items()
# #                 if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
# #             }

# #             # Log filtered PII
# #             print(f"Filtered PII for level {redaction_level}: {filtered_pii}")

# #             # Mask sensitive information in the image using filtered PII and redaction level
# #             masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
# #             redacted_image_path = os.path.join(REDACTED_FOLDER, "redacted_image.png")
# #             masked_image.save(redacted_image_path)
# #             redacted_file_url = f"/download/{os.path.basename(redacted_image_path)}"
# #         except Exception as e:
# #             return jsonify({"error": f"Cannot process file: {str(e)}"}), 400

# #     # Redact sensitive information in the text using filtered PII
# #     redacted_text = redact_text(text, filtered_pii)

# #     # Emit a real-time alert to the client with filtered PII
# #     socketio.emit("pii_detected", {"detected_pii": filtered_pii})

# #     return jsonify(
# #         {
# #             "text": text,
# #             "redacted_text": redacted_text,
# #             "detected_pii": filtered_pii,
# #             "redacted_file_url": redacted_file_url,  # URL to download the redacted file
# #         }
# #     )
# # # Route to download redacted files
# # @app.route("/download/<filename>", methods=["GET"])
# # def download_file(filename):
# #     return send_from_directory(REDACTED_FOLDER, filename, as_attachment=True)


# # if __name__ == "__main__":
# #     socketio.run(app, debug=True)  # Use socketio.run instead of app.run
# import os
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from flask_socketio import SocketIO, emit
# import pytesseract
# from pdf2image import convert_from_bytes
# from PIL import Image
# import cv2
# import numpy as np
# import io
# from utils.pii_detector import detect_pii
# import speech_recognition as sr
# import re
# from presidio_analyzer import AnalyzerEngine
# import winsound

# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes

# # Initialize SocketIO without specifying async_mode
# socketio = SocketIO(app, cors_allowed_origins="*")

# # Set the Poppler path (update this to your Poppler bin directory)
# POPPLER_PATH = (
#     r"C:\Users\aadil\Desktop\poppler-24.08.0\Library\bin"
# )

# # Folder to store redacted documents
# REDACTED_FOLDER = "redacted_documents"
# os.makedirs(REDACTED_FOLDER, exist_ok=True)

# # Initialize Presidio Analyzer
# analyzer = AnalyzerEngine()

# # Context References: Phrases that indicate upcoming PII
# CONTEXT_REFERENCES = {
#     "CREDIT_CARD_NUMBER": [
#         "my credit card number is", 
#         "here is my credit card", 
#         "this is my card number", 
#         "use this card for payment",
#         "enter my credit card details"
#     ],
#     "DEBIT_CARD_NUMBER": [
#         "my debit card number is", 
#         "here is my debit card", 
#         "this is my ATM card number", 
#         "use this for the transaction"
#     ],
#     "AADHAAR_NUMBER": [
#         "my Aadhaar number is", 
#         "Aadhaar number is", 
#         "this is my UIDAI number", 
#         "provide my Aadhaar"
#     ],
#     "PAN_NUMBER": [
#         "my PAN number is", 
#         "here is my PAN", 
#         "this is my tax ID"
#     ],
#     "PASSPORT_NUMBER": [
#         "my passport number is", 
#         "passport details are", 
#         "this is my travel document number"
#     ],
#     "DRIVING_LICENSE": [
#         "my driving license number is", 
#         "license details are", 
#         "this is my DL number"
#     ],
#     "BANK_ACCOUNT_NUMBER": [
#         "my bank account number is", 
#         "account number is", 
#         "deposit it in this account",
#         "transfer money to this account"
#     ],
#     "IFSC_CODE": [
#         "the IFSC code is", 
#         "use this bank IFSC", 
#         "branch IFSC is"
#     ],
#     "UPI_ID": [
#         "send money to this UPI", 
#         "my UPI ID is", 
#         "pay me at this UPI handle"
#     ],
#     "PHONE_NUMBER": [
#         "my phone number is", 
#         "here is my contact number", 
#         "call me at this number"
#     ],
#     "EMAIL_ADDRESS": [
#         "my email address is", 
#         "send it to my email", 
#         "contact me at this email"
#     ]
# }

# # Custom PII Categories with Regular Expressions
# PII_CATEGORIES = {
#     "AADHAAR_NUMBER": r"\b\d{4}\s\d{4}\s\d{4}\b",
#     "PAN_NUMBER": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
#     "PASSPORT_NUMBER": r"\b[A-Z]{1}[0-9]{7}\b",
#     "DRIVING_LICENSE": r"\b[A-Z]{2}\d{2}\s\d{4}\s\d{7}\b",
#     "CREDIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
#     "DEBIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
#     "BANK_ACCOUNT_NUMBER": r"\b\d{9,18}\b",
#     "IFSC_CODE": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
#     "UPI_ID": r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b",
#     "PHONE_NUMBER": r"\b\d{10}\b",
#     "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
# }

# # Function to detect PII in text
# def detect_pii_audio(text):
#     detected_pii = []
    
#     # Use Presidio for built-in PII detection
#     results = analyzer.analyze(text=text, language="en")

#     # Collect detected entities from Presidio
#     for r in results:
#         detected_pii.append((r.entity_type, text[r.start:r.end]))

#     # Use regex to detect additional PII
#     for category, pattern in PII_CATEGORIES.items():
#         matches = re.finditer(pattern, text)
#         for match in matches:
#             detected_pii.append((category, match.group()))

#     return detected_pii

# # Function to detect context-based PII hints
# def detect_context(text):
#     for pii_type, phrases in CONTEXT_REFERENCES.items():
#         for phrase in phrases:
#             if phrase.lower() in text.lower():
#                 return pii_type  # Return the type of PII being hinted
#     return None

# # Function to preprocess image for OCR
# def preprocess_image(image):
#     """
#     Preprocess the image to improve OCR accuracy.
#     """
#     # Convert to grayscale
#     gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
#     # Apply Gaussian blur
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#     # Apply binary thresholding
#     _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     return Image.fromarray(thresholded)

# # Function to redact text
# def redact_text(text, detected_pii):
#     """
#     Redact sensitive information in the text.
#     """
#     for pii_type, values in detected_pii.items():
#         for value in values:
#             text = text.replace(value, "[REDACTED]")
#     return text

# # Function to mask image based on detected PII
# def mask_image(image, detected_pii, redaction_level):
#     """
#     Mask sensitive information in the image based on the selected redaction level.
#     """
#     from utils.pii_detector import PII_LEVEL_MAPPING

#     # Define the order of redaction levels
#     levels_order = ['basic', 'intermediate', 'critical']

#     # Convert PIL image to OpenCV format
#     image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

#     # Use Tesseract to detect text and their bounding boxes
#     custom_config = r"--oem 3 --psm 6"
#     data = pytesseract.image_to_data(
#         image, output_type=pytesseract.Output.DICT, config=custom_config
#     )

#     # Loop through detected text and mask PII
#     for i in range(len(data["text"])):
#         text = data["text"][i].strip()  # Remove leading/trailing whitespace
#         if text:  # Only process non-empty text
#             for pii_type, values in detected_pii.items():
#                 # Check if the PII type matches the selected redaction level
#                 if PII_LEVEL_MAPPING.get(pii_type, "basic") in levels_order[: levels_order.index(redaction_level) + 1]:
#                     for value in values:
#                         # Check if the detected text contains the PII value
#                         if value.strip() in text:
#                             # Get the bounding box coordinates
#                             x, y, w, h = (
#                                 data["left"][i],
#                                 data["top"][i],
#                                 data["width"][i],
#                                 data["height"][i],
#                             )
#                             # Mask the area
#                             cv2.rectangle(
#                                 image_cv, (x, y), (x + w, y + h), (0, 0, 0), -1
#                             )  # Black out the area

#     return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))

# # Route for uploading and processing documents
# @app.route("/upload", methods=["POST"])
# def upload_document():
#     if "file" not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files["file"]
#     if file.filename == "":
#         return jsonify({"error": "No file selected"}), 400

#     # Get the selected redaction level from the form data
#     redaction_level = request.form.get("redaction_level", "basic").lower()
#     levels_order = ["basic", "intermediate", "critical"]
#     if redaction_level not in levels_order:
#         redaction_level = "basic"  # Default to basic if invalid level is provided

#     # Read the file into memory
#     file_bytes = file.read()

#     # Check if the file is a PDF
#     if file.filename.lower().endswith(".pdf"):
#         # Convert PDF to images
#         images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
#         text = ""
#         all_detected_pii = {}  # Accumulate detected PII across all pages
#         redacted_images = []

#         for image in images:
#             # Preprocess the image
#             processed_image = preprocess_image(image)
#             # Extract text using OCR
#             custom_config = r"--oem 3 --psm 6"
#             extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
#             text += extracted_text + "\n"

#             # Detect PII in the extracted text
#             detected_pii = detect_pii(extracted_text)

#             # Accumulate detected PII across all pages
#             for pii_type, values in detected_pii.items():
#                 if pii_type in all_detected_pii:
#                     all_detected_pii[pii_type].extend(v for v in values if v not in all_detected_pii[pii_type])
#                 else:
#                     all_detected_pii[pii_type] = values.copy()

#         # Filter detected PII based on the selected redaction level
#         from utils.pii_detector import PII_LEVEL_MAPPING
#         filtered_pii = {
#             pii_type: values
#             for pii_type, values in all_detected_pii.items()
#             if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
#         }

#         # Mask sensitive information in the images using filtered PII and redaction level
#         for image in images:
#             masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
#             redacted_images.append(masked_image)

#         # Save redacted images as a PDF
#         from fpdf import FPDF

#         pdf = FPDF()
#         for redacted_image in redacted_images:
#             redacted_image_path = os.path.join(REDACTED_FOLDER, "temp.png")
#             redacted_image.save(redacted_image_path)
#             pdf.add_page()
#             pdf.image(redacted_image_path, x=10, y=10, w=190)
#             os.remove(redacted_image_path)  # Clean up temporary files
#         redacted_pdf_path = os.path.join(REDACTED_FOLDER, "redacted_document.pdf")
#         pdf.output(redacted_pdf_path)
#         redacted_file_url = f"/download/{os.path.basename(redacted_pdf_path)}"

#     else:
#         # Handle image files (JPEG, PNG, etc.)
#         try:
#             image = Image.open(io.BytesIO(file_bytes))
#             # Preprocess the image
#             processed_image = preprocess_image(image)
#             # Extract text using OCR
#             custom_config = r"--oem 3 --psm 6"
#             extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
#             text = extracted_text

#             # Detect PII in the extracted text
#             detected_pii = detect_pii(extracted_text)

#             # Filter detected PII based on the selected redaction level
#             from utils.pii_detector import PII_LEVEL_MAPPING
#             filtered_pii = {
#                 pii_type: values
#                 for pii_type, values in detected_pii.items()
#                 if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
#             }

#             # Mask sensitive information in the image using filtered PII and redaction level
#             masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
#             redacted_image_path = os.path.join(REDACTED_FOLDER, "redacted_image.png")
#             masked_image.save(redacted_image_path)
#             redacted_file_url = f"/download/{os.path.basename(redacted_image_path)}"
#         except Exception as e:
#             return jsonify({"error": f"Cannot process file: {str(e)}"}), 400

#     # Redact sensitive information in the text using filtered PII
#     redacted_text = redact_text(text, filtered_pii)

#     # Emit a real-time alert to the client with filtered PII
#     socketio.emit("pii_detected", {"detected_pii": filtered_pii})

#     return jsonify(
#         {
#             "text": text,
#             "redacted_text": redacted_text,
#             "detected_pii": filtered_pii,
#             "redacted_file_url": redacted_file_url,  # URL to download the redacted file
#         }
#     )

# @app.route("/process_text", methods=["POST"])
# def process_text():
#     data = request.json
#     text = data.get("text")
#     redaction_level = data.get("redaction_level", "basic")

#     # Detect PII in the text
#     detected_pii = detect_pii_audio(text)
#     context_pii = detect_context(text)

#     # Redact sensitive information in the text
#     redacted_text = text
#     for pii_type, value in detected_pii:
#         redacted_text = redacted_text.replace(value[1], "[REDACTED]")

#     # Save the redacted text to a file
#     redacted_file_path = os.path.join(REDACTED_FOLDER, "redacted_transcription.txt")
#     with open(redacted_file_path, "w") as f:
#         f.write(redacted_text)

#     redacted_file_url = f"/download/{os.path.basename(redacted_file_path)}"

#     return jsonify(
#         {
#             "text": text,
#             "redacted_text": redacted_text,
#             "detected_pii": detected_pii,
#             "context_pii": context_pii,
#             "redacted_file_url": redacted_file_url,
#         }
#     )
# # Route for uploading and processing audio files
# @app.route("/upload_audio", methods=["POST"])
# def upload_audio():
#     if "file" not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files["file"]
#     if file.filename == "":
#         return jsonify({"error": "No file selected"}), 400

#     # Read the audio file
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(file) as source:
#         audio = recognizer.record(source)

#     try:
#         # Transcribe the audio
#         text = recognizer.recognize_google(audio)
#         print("Transcription:", text)

#         # Detect PII in the transcribed text
#         detected_pii = detect_pii_audio(text)
#         context_pii = detect_context(text)

#         # Redact sensitive information in the text
#         redacted_text = text
#         for pii_type, value in detected_pii:
#             redacted_text = redacted_text.replace(value[1], "[REDACTED]")

#         # Save the redacted text to a file
#         redacted_file_path = os.path.join(REDACTED_FOLDER, "redacted_transcription.txt")
#         with open(redacted_file_path, "w") as f:
#             f.write(redacted_text)

#         redacted_file_url = f"/download/{os.path.basename(redacted_file_path)}"

#         return jsonify(
#             {
#                 "text": text,
#                 "redacted_text": redacted_text,
#                 "detected_pii": detected_pii,
#                 "context_pii": context_pii,
#                 "redacted_file_url": redacted_file_url,
#             }
#         )
#     except sr.UnknownValueError:
#         return jsonify({"error": "Could not understand the audio"}), 400
#     except sr.RequestError:
#         return jsonify({"error": "API unavailable"}), 500

# # Route to download redacted files
# @app.route("/download/<filename>", methods=["GET"])
# def download_file(filename):
#     return send_from_directory(REDACTED_FOLDER, filename, as_attachment=True)

# if __name__ == "__main__":
#     socketio.run(app, debug=True)  # Use socketio.run instead of app.run
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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize SocketIO without specifying async_mode
socketio = SocketIO(app, cors_allowed_origins="*")

# Set the Poppler path (update this to your Poppler bin directory)
POPPLER_PATH = (
    r"C:\Users\babusha kolhe\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
)

# Folder to store redacted documents
REDACTED_FOLDER = "redacted_documents"
os.makedirs(REDACTED_FOLDER, exist_ok=True)

# Initialize Presidio Analyzer
analyzer = AnalyzerEngine()

def play_alert_sound():
    frequency = 1000  # Set frequency to 1000 Hzq
    duration = 500  # Set duration to 500 milliseconds
    winsound.Beep(frequency, duration)  # Play sound


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
def detect_pii_audio(text):
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

    if detected_pii:
        print("\n⚠️ PII Detected! Sensitive Information Found:")
        for entity, value in detected_pii:
            print(f"🔴 Entity: {entity}, Text: {value}")
        
        play_alert_sound()  # Play buzzer when PII is detected
        return True

    return False
    #return detected_pii

# Function to detect context-based PII hints
def detect_context(text):
    for pii_type, phrases in CONTEXT_REFERENCES.items():
        for phrase in phrases:
            if phrase.lower() in text.lower():
                print(f"⚠️ Potential PII Context Detected: {pii_type}")
                play_alert_sound()
                return pii_type  # Return the type of PII being hinted
    return None

# Function to preprocess image for OCR
def preprocess_image(image):
    """
    Preprocess the image to improve OCR accuracy.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply binary thresholding
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresholded)

# Function to redact text
def redact_text(text, detected_pii):
    """
    Redact sensitive information in the text.
    """
    for pii_type, values in detected_pii.items():
        for value in values:
            text = text.replace(value, "[REDACTED]")
    return text

# Function to mask image based on detected PII
def mask_image(image, detected_pii, redaction_level):
    """
    Mask sensitive information in the image based on the selected redaction level.
    """
    from utils.pii_detector import PII_LEVEL_MAPPING

    # Define the order of redaction levels
    levels_order = ['basic', 'intermediate', 'critical']

    # Convert PIL image to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Use Tesseract to detect text and their bounding boxes
    custom_config = r"--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, config=custom_config
    )

    # Loop through detected text and mask PII
    for i in range(len(data["text"])):
        text = data["text"][i].strip()  # Remove leading/trailing whitespace
        if text:  # Only process non-empty text
            for pii_type, values in detected_pii.items():
                # Check if the PII type matches the selected redaction level
                if PII_LEVEL_MAPPING.get(pii_type, "basic") in levels_order[: levels_order.index(redaction_level) + 1]:
                    for value in values:
                        # Check if the detected text contains the PII value
                        if value.strip() in text:
                            # Get the bounding box coordinates
                            x, y, w, h = (
                                data["left"][i],
                                data["top"][i],
                                data["width"][i],
                                data["height"][i],
                            )
                            # Mask the area
                            cv2.rectangle(
                                image_cv, (x, y), (x + w, y + h), (0, 0, 0), -1
                            )  # Black out the area

    return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))

# Route for uploading and processing documents
@app.route("/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Get the selected redaction level from the form data
    redaction_level = request.form.get("redaction_level", "basic").lower()
    levels_order = ["basic", "intermediate", "critical"]
    if redaction_level not in levels_order:
        redaction_level = "basic"  # Default to basic if invalid level is provided

    # Read the file into memory
    file_bytes = file.read()

    # Check if the file is a PDF
    if file.filename.lower().endswith(".pdf"):
        # Convert PDF to images
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
        text = ""
        all_detected_pii = {}  # Accumulate detected PII across all pages
        redacted_images = []

        for image in images:
            # Preprocess the image
            processed_image = preprocess_image(image)
            # Extract text using OCR
            custom_config = r"--oem 3 --psm 6"
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
            text += extracted_text + "\n"

            # Detect PII in the extracted text
            detected_pii = detect_pii(extracted_text)

            # Accumulate detected PII across all pages
            for pii_type, values in detected_pii.items():
                if pii_type in all_detected_pii:
                    all_detected_pii[pii_type].extend(v for v in values if v not in all_detected_pii[pii_type])
                else:
                    all_detected_pii[pii_type] = values.copy()

        # Filter detected PII based on the selected redaction level
        from utils.pii_detector import PII_LEVEL_MAPPING
        filtered_pii = {
            pii_type: values
            for pii_type, values in all_detected_pii.items()
            if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
        }

        # Mask sensitive information in the images using filtered PII and redaction level
        for image in images:
            masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
            redacted_images.append(masked_image)

        # Save redacted images as a PDF
        from fpdf import FPDF

        pdf = FPDF()
        for redacted_image in redacted_images:
            redacted_image_path = os.path.join(REDACTED_FOLDER, "temp.png")
            redacted_image.save(redacted_image_path)
            pdf.add_page()
            pdf.image(redacted_image_path, x=10, y=10, w=190)
            os.remove(redacted_image_path)  # Clean up temporary files
        redacted_pdf_path = os.path.join(REDACTED_FOLDER, "redacted_document.pdf")
        pdf.output(redacted_pdf_path)
        redacted_file_url = f"/download/{os.path.basename(redacted_pdf_path)}"

    else:
        # Handle image files (JPEG, PNG, etc.)
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Preprocess the image
            processed_image = preprocess_image(image)
            # Extract text using OCR
            custom_config = r"--oem 3 --psm 6"
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
            text = extracted_text

            # Detect PII in the extracted text
            detected_pii = detect_pii(extracted_text)

            # Filter detected PII based on the selected redaction level
            from utils.pii_detector import PII_LEVEL_MAPPING
            filtered_pii = {
                pii_type: values
                for pii_type, values in detected_pii.items()
                if levels_order.index(PII_LEVEL_MAPPING.get(pii_type, "basic")) <= levels_order.index(redaction_level)
            }

            # Mask sensitive information in the image using filtered PII and redaction level
            masked_image = mask_image(image, filtered_pii, redaction_level)  # Pass redaction_level here
            redacted_image_path = os.path.join(REDACTED_FOLDER, "redacted_image.png")
            masked_image.save(redacted_image_path)
            redacted_file_url = f"/download/{os.path.basename(redacted_image_path)}"
        except Exception as e:
            return jsonify({"error": f"Cannot process file: {str(e)}"}), 400

    # Redact sensitive information in the text using filtered PII
    redacted_text = redact_text(text, filtered_pii)

    # Emit a real-time alert to the client with filtered PII
    socketio.emit("pii_detected", {"detected_pii": filtered_pii})

    return jsonify(
        {
            "text": text,
            "redacted_text": redacted_text,
            "detected_pii": filtered_pii,
            "redacted_file_url": redacted_file_url,  # URL to download the redacted file
        }
    )

# Route for live transcription
@app.route("/live_transcription", methods=["GET"])
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
                if detect_pii_audio(text):
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

    return jsonify({"status": "Listening completed"}), 200

# Route to download redacted files
@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(REDACTED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)  # Use socketio.run instead of app.run