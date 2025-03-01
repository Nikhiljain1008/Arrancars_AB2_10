import os

# Define project structure
project_structure = {
    "PII-Redaction-WebApp": [
        "backend",
        "frontend/static",
        "models",
        "logs"
    ],
    "backend": [
        "templates",
        "static"
    ]
}

# Define files to create
files_to_create = {
    "PII-Redaction-WebApp/README.md": "# PII Detection & Redaction Web App\n",
    "PII-Redaction-WebApp/requirements.txt": "Flask\nTesseract\nspacy\npdf2image\npytesseract\nopencv-python\n",
    
    # Backend files
    "backend/app.py": '"""\nFlask API for PII Detection and Redaction\n"""\nfrom flask import Flask\napp = Flask(__name__)\n@app.route("/")\ndef home():\n    return "PII Detection API Running!"\nif __name__ == "__main__":\n    app.run(debug=True)',
    "backend/ocr.py": '"""\nOCR Processing for Document Uploads\n"""\nimport pytesseract\nfrom PIL import Image\n\ndef extract_text(image_path):\n    return pytesseract.image_to_string(Image.open(image_path))\n',
    "backend/pii_detection.py": '"""\nPII Detection Using Regex & NER\n"""\nimport re\nimport spacy\n\nnlp = spacy.load("en_core_web_sm")\n\n# Regex patterns for common PII\ndef detect_pii(text):\n    patterns = {\n        "Aadhaar": r"\\b\\d{4} \\d{4} \\d{4}\\b",\n        "PAN": r"\\b[A-Z]{5}[0-9]{4}[A-Z]\\b",\n        "Phone": r"\\b\\d{10}\\b"\n    }\n    matches = {key: re.findall(pattern, text) for key, pattern in patterns.items()}\n    return matches\n',
    
    # Frontend files
    "frontend/index.html": '<!DOCTYPE html>\n<html>\n<head>\n    <title>PII Redaction App</title>\n</head>\n<body>\n    <h1>Upload Document for PII Detection</h1>\n    <input type="file" id="fileInput">\n    <button onclick="uploadFile()">Submit</button>\n    <script src="static/script.js"></script>\n</body>\n</html>',
    "frontend/static/script.js": 'function uploadFile() { alert("File uploaded! PII Detection coming soon."); }',
    "frontend/static/styles.css": "body { font-family: Arial, sans-serif; }"
}

# Create directories
for base_folder, subdirs in project_structure.items():
    os.makedirs(base_folder, exist_ok=True)
    for subdir in subdirs:
        os.makedirs(os.path.join(base_folder, subdir), exist_ok=True)

# Create files with content
for file_path, content in files_to_create.items():
    with open(file_path, "w") as file:
        file.write(content)

print("✅ Project structure created successfully! Start coding 🚀")
