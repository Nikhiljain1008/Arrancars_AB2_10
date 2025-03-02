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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize SocketIO without specifying async_mode
socketio = SocketIO(app, cors_allowed_origins="*")

# Set the Poppler path (update this to your Poppler bin directory)
POPPLER_PATH = (
    r"C:\Users\aadil\Desktop\poppler-24.08.0\Library\bin"
)

# Folder to store redacted documents
REDACTED_FOLDER = "redacted_documents"
os.makedirs(REDACTED_FOLDER, exist_ok=True)


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


def redact_text(text, detected_pii):
    """
    Redact sensitive information in the text.
    """
    for pii_type, values in detected_pii.items():
        for value in values:
            text = text.replace(value, "[REDACTED]")
    return text


def mask_image(image, detected_pii):
    """
    Mask sensitive information in the image.
    """
    # Convert PIL image to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Use Tesseract to detect text and their bounding boxes
    custom_config = r"--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, config=custom_config
    )

    # Loop through detected text and mask PII
    for i in range(len(data["text"])):
        text = data["text"][i]
        for pii_type, values in detected_pii.items():
            for value in values:
                if value in text:
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

    # Read the file into memory
    file_bytes = file.read()

    # Check if the file is a PDF
    if file.filename.lower().endswith(".pdf"):
        # Convert PDF to images
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
        text = ""
        redacted_images = []
        for image in images:
            # Preprocess the image
            processed_image = preprocess_image(image)
            # Extract text using OCR
            custom_config = r"--oem 3 --psm 6"  # OEM 3 = LSTM, PSM 6 = Assume a single uniform block of text
            extracted_text = pytesseract.image_to_string(
                processed_image, config=custom_config
            )
            text += extracted_text + "\n"

            # Detect PII in the extracted text
            detected_pii = detect_pii(extracted_text)

            # Mask sensitive information in the image
            masked_image = mask_image(image, detected_pii)
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
            extracted_text = pytesseract.image_to_string(
                processed_image, config=custom_config
            )
            text = extracted_text

            # Detect PII in the extracted text
            detected_pii = detect_pii(extracted_text)

            # Mask sensitive information in the image
            masked_image = mask_image(image, detected_pii)
            redacted_image_path = os.path.join(REDACTED_FOLDER, "redacted_image.png")
            masked_image.save(redacted_image_path)
            redacted_file_url = f"/download/{os.path.basename(redacted_image_path)}"
        except Exception as e:
            return jsonify({"error": f"Cannot process file: {str(e)}"}), 400

    # Redact sensitive information in the text
    redacted_text = redact_text(text, detected_pii)

    # Emit a real-time alert to the client
    socketio.emit("pii_detected", {"detected_pii": detected_pii})

    return jsonify(
        {
            "text": text,
            "redacted_text": redacted_text,
            "detected_pii": detected_pii,
            "redacted_file_url": redacted_file_url,  # URL to download the redacted file
        }
    )


# Route to download redacted files
@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(REDACTED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)  # Use socketio.run instead of app.run