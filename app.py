import cv2
import pytesseract
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

# --- Define PII Categories ---
PII_CATEGORIES = {
    "AADHAAR_NUMBER": r"\b\d{4}\s\d{4}\s\d{4}\b",
    "PAN_NUMBER": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "VOTER_ID": r"\b[A-Z]{3}[0-9]{7}\b",
    "DRIVING_LICENSE": r"\b[A-Z]{2}\d{2}\s\d{4}\s\d{7}\b",
    "PASSPORT_NUMBER": r"\b[A-Z]{1}[0-9]{7}\b",
    "CREDIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "DEBIT_CARD_NUMBER": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "BANK_ACCOUNT_NUMBER": r"\b\d{9,18}\b",
    "IFSC_CODE": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "UPI_ID": r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b",
    "PHONE_NUMBER": r"\b\d{10}\b",
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "PINCODE": r"\b\d{6}\b",
    "GST_NUMBER": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b",
    "CIN_NUMBER": r"\b[LU]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b",
    "ESIC_NUMBER": r"\b\d{2}-\d{3}-\d{6}-\d\b",
    "PF_NUMBER": r"\b[A-Z]{2}/\d{5}/\d{7}\b"
}

# --- Initialize Presidio Analyzer ---
analyzer = AnalyzerEngine()

# Add all custom PII recognizers dynamically
for entity, regex in PII_CATEGORIES.items():
    pattern = Pattern(name=f"{entity}_pattern", regex=regex, score=0.9)
    recognizer = PatternRecognizer(supported_entity=entity, patterns=[pattern])
    analyzer.registry.add_recognizer(recognizer)

# --- Image Processing and OCR ---
def process_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    words, boxes = [], []
    for i in range(len(ocr_data['text'])):
        if int(ocr_data['conf'][i]) > 60:  # Filter low-confidence detections
            word = ocr_data['text'][i].strip()
            if word:
                left, top, width, height = (
                    ocr_data['left'][i], ocr_data['top'][i], 
                    ocr_data['width'][i], ocr_data['height'][i]
                )
                words.append(word)
                boxes.append((left, top, left + width, top + height))
    
    return image, words, boxes

# --- Text Analysis and Redaction ---
def analyze_and_redact(image, words, boxes):
    full_text = ' '.join(words)
    word_positions = []
    current_pos = 0

    for word in words:
        start = current_pos
        end = start + len(word)
        word_positions.append((start, end))
        current_pos += len(word) + 1  

    results = analyzer.analyze(text=full_text, language='en')

    for result in results:
        entity_start, entity_end = result.start, result.end
        redact_boxes = []
        for idx, (start, end) in enumerate(word_positions):
            if start < entity_end and end > entity_start:
                redact_boxes.append(boxes[idx])

        if redact_boxes:
            x_min, y_min = min(box[0] for box in redact_boxes), min(box[1] for box in redact_boxes)
            x_max, y_max = max(box[2] for box in redact_boxes), max(box[3] for box in redact_boxes)
            
            # Draw redaction box (black rectangle)
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 0, 0), -1)
            print(f"Redacted {result.entity_type}: {full_text[entity_start:entity_end]}")
    
    return image

# --- Main Execution ---
image_path = r"C:\Users\91738\Downloads\Pccoe AB2 hackathon\Id-card .jpg"
output_path = "redacted_output.jpg"

image, words, boxes = process_image(image_path)
redacted_image = analyze_and_redact(image, words, boxes)

cv2.imwrite(output_path, redacted_image)
cv2.imshow("Redacted Image", redacted_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
