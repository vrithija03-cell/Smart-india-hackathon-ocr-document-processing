import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
from datetime import datetime
import json

# Tesseract location
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def preprocess_image(image_path):
    """Improve the image before OCR."""
    image = Image.open(image_path)

    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2)
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


def extract_text(image_path):
    """Extract text and calculate OCR confidence."""

    image = preprocess_image(image_path)

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT
    )

    words = []
    confidences = []

    for i in range(len(data["text"])):

        word = data["text"][i].strip()

        try:
            confidence = float(data["conf"][i])
        except ValueError:
            confidence = -1

        if word and confidence >= 0:
            words.append(word)
            confidences.append(confidence)

    text = " ".join(words)

    if confidences:
        average_confidence = sum(confidences) / len(confidences)
    else:
        average_confidence = 0

    return text, average_confidence


def detect_document_type(text):
    """Detect the likely document type."""

    text_upper = text.upper()

    if "AADHAAR" in text_upper or "UNIQUE IDENTIFICATION" in text_upper:
        return "Aadhaar"

    elif (
        "INCOME TAX DEPARTMENT" in text_upper
        or "PERMANENT ACCOUNT NUMBER" in text_upper
    ):
        return "PAN"

    elif (
        "DRIVING LICENCE" in text_upper
        or "DRIVING LICENSE" in text_upper
    ):
        return "Driving Licence"

    elif "PASSPORT" in text_upper:
        return "Passport"

    else:
        return "Unknown"


def validate_dob(dob):
    """Check whether the extracted DOB is a valid date."""

    if not dob:
        return False

    # Try different common date formats
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y"
    ]

    for date_format in formats:
        try:
            datetime.strptime(dob, date_format)
            return True
        except ValueError:
            continue

    return False


def extract_fields(text):
    """Extract important fields from OCR text."""

    fields = {
        "name": None,
        "date_of_birth": None,
        "document_id": None
    }

    # Correct common OCR mistakes
    text = text.replace("Narne", "Name")
    text = text.replace("D0B", "DOB")
    text = text.replace("Docurnent", "Document")

    # -------------------------
    # Find Name
    # -------------------------
    name_match = re.search(
        r"Name\s*[:\-]?\s*(.*?)(?=\s+"
        r"(?:DOB|Date of Birth|Birth Date)\b|$)",
        text,
        re.IGNORECASE
    )

    if name_match:
        fields["name"] = name_match.group(1).strip()

    # -------------------------
    # Find Date of Birth
    # -------------------------
    dob_match = re.search(
        r"(?:DOB|Date of Birth|Birth Date)\s*[:\-]?\s*"
        r"([0-9O@IlS]{1,2}\s*[/-]\s*"
        r"[0-9O@IlS]{1,2}\s*[/-]\s*"
        r"[0-9O@IlS]{2,4})",
        text,
        re.IGNORECASE
    )

    if dob_match:
        dob = dob_match.group(1)

        # Correct OCR mistakes ONLY inside DOB
        dob = dob.replace("@", "0")
        dob = dob.replace("O", "0")
        dob = dob.replace("I", "1")
        dob = dob.replace("l", "1")

        dob = re.sub(r"\s+", "", dob)

        fields["date_of_birth"] = dob

    # -------------------------
    # Find Document ID
    # -------------------------
    id_match = re.search(
        r"(?:ID|Document ID|Document Number)\s*[:\-]?\s*"
        r"([A-Za-z0-9]+)",
        text,
        re.IGNORECASE
    )

    if id_match:
        fields["document_id"] = id_match.group(1)

    return fields


# =========================
# MAIN PROGRAM
# =========================

if __name__ == "__main__":

    image_path = "documents/test.png"

    # OCR
    text, ocr_confidence = extract_text(image_path)

    print("\n========== RAW OCR ==========")
    print(text)

    # OCR confidence
    print("\n========== OCR CONFIDENCE ==========")
    print("Average OCR Confidence:",
          round(ocr_confidence, 2), "%")

    # Document type
    document_type = detect_document_type(text)

    print("\n========== DOCUMENT TYPE ==========")
    print("Document Type:", document_type)

    # Field extraction
    fields = extract_fields(text)

    # DOB validation
    fields["dob_valid"] = validate_dob(
        fields["date_of_birth"]
    )

    # Add OCR confidence
    fields["ocr_confidence"] = round(
        ocr_confidence, 2
    )

    # Add document type
    fields["document_type"] = document_type

    print("\n========== EXTRACTED FIELDS ==========")
    print("Name:", fields["name"])
    print("Date of Birth:", fields["date_of_birth"])
    print("Document ID:", fields["document_id"])
    print("DOB Valid:", fields["dob_valid"])

    # Save JSON
    with open("ocr_result.json", "w") as file:
        json.dump(fields, file, indent=4)

    print("\nOCR result saved to ocr_result.json")