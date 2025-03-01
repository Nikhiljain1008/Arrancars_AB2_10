
import os
import cv2
import pytesseract
import pymupdf as fitz
 # PyMuPDF for PDF text extraction
from pdf2image import convert_from_path
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pii_detection import detect_pii_and_redact

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure Tesseract is correctly set up
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Change if needed


def allowed_file(filename):
    """Check if the uploaded file has a valid extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    """Preprocess the image to improve OCR accuracy, especially for blurry text."""
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Deblur using Unsharp Masking
    gaussian = cv2.GaussianBlur(enhanced, (0, 0), 3)
    sharpened = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)

    # Denoise using Bilateral Filter
    denoised = cv2.bilateralFilter(sharpened, 9, 75, 75)

    # Adaptive Thresholding for better contrast
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)

    return binary


def extract_text_from_image(image_path):
    """Extract text from an image using optimized settings for blurry text."""
    img = preprocess_image(image_path)  # Apply advanced preprocessing
    custom_config = '--psm 6 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"'
    extracted_text = pytesseract.image_to_string(img, config=custom_config, lang='eng')
    return extracted_text.strip()



def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using direct text extraction and OCR fallback."""
    text = ""

    try:
        # Attempt direct text extraction
        doc = fitz.open(pdf_path)
        extracted_text = "\n".join([page.get_text("text") for page in doc if page.get_text("text").strip()])
        
        if extracted_text.strip():  # If direct extraction works, return
            print(f"Direct text extracted from {pdf_path}")
            return extracted_text.strip()
        
        print(f"No direct text found in {pdf_path}, switching to OCR...")
        
    except Exception as e:
        print(f"PDF text extraction error: {e}")

    # If direct extraction fails, use OCR
    try:
        images = convert_from_path(pdf_path, dpi=300)  # High DPI for better OCR
        for img in images:
            img_np = np.array(img)  # Convert PIL image to NumPy array
            img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
            extracted_text = pytesseract.image_to_string(img_gray, config='--psm 6', lang='eng')
            text += extracted_text + "\n"
    
    except Exception as e:
        print(f"PDF OCR error: {e}")

    return text.strip()


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads and extract text."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Extract text based on file type
        extracted_text = ""
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            extracted_text = extract_text_from_image(file_path)
        elif filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)

        # Log extracted text for debugging
        print(f"Extracted Text from {filename}:\n{extracted_text}")

        return jsonify({"filename": filename, "extracted_text": extracted_text})

    return jsonify({"error": "Invalid file type"}), 400
@app.route('/detect_pii', methods=['POST'])
def detect_pii_route():
    """API Endpoint to detect PII in uploaded text."""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Invalid request. 'text' field is required"}), 400

        text = data.get("text", "")
        pii_level = data.get("pii_level", "critical")  # Default to 'critical'
        pii_results = detect_pii_and_redact(text, pii_level)  # Ensure detect_pii function exists

        return jsonify({"detect_pii": pii_results}), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
