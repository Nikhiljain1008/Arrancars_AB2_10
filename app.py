from presidio_analyzer import AnalyzerEngine

def detect_pii_presidio():
    analyzer = AnalyzerEngine()

    # Get OCR-extracted text as input
    text = input("Enter the OCR-extracted text: ")

    # Detect ALL available entities
    results = analyzer.analyze(text=text, language="en")

    if not results:
        print("No PII detected.")
        return

    print("\nDetected PII Entities:")
    for r in results:
        print(f"Entity: {r.entity_type}, Score: {r.score:.2f}, Start: {r.start}, End: {r.end}, Text: {text[r.start:r.end]}")

# Run Presidio PII detection
detect_pii_presidio()

# from transformers import pipeline

# def detect_pii_huggingface():
#     # Load Hugging Face model for PII detection
#     nlp = pipeline("ner", model="obi/deid_roberta_i2b2", aggregation_strategy="simple")

#     # Get OCR-extracted text as input
#     text = input("Enter the OCR-extracted text: ")

#     results = nlp(text)

#     if not results:
#         print("No PII detected.")
#         return

#     print("\nDetected PII Entities:")
#     for entity in results:
#         print(f"Entity: {entity['word']}, Label: {entity['entity_group']}, Confidence: {entity['score']:.2f}")

# # Run Hugging Face PII detection
# detect_pii_huggingface()
