"""
OCR Processing for Document Uploads
"""
import pytesseract
from PIL import Image

def extract_text(image_path):
    return pytesseract.image_to_string(Image.open(image_path))
