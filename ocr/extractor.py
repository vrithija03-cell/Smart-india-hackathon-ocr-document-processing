import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
from datetime import datetime
import json

from .tamper_detection import analyze_tampering
from .risk_score import calculate_risk_score


# =========================================================
# TESSERACT LOCATION
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_path):
    """Improve the image before OCR."""

    image = Image.open(image_path)

    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2)
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


# =========================================================
# OCR EXTRACTION
# =========================================================

def extract_text(image_path):
    """Extract text and confidence for every OCR word."""

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

    return text, average_confidence, words, confidences


# =========================================================
# FIELD CONFIDENCE
# =========================================================

def calculate_field_confidence(words, confidences, field):
    """Calculate OCR confidence for Name or DOB."""

    clean_words = [
        re.sub(r"[^a-zA-Z0-9]", "", word).lower()
        for word in words
    ]

    # -------------------------
    # NAME CONFIDENCE
    # -------------------------

    if field.lower() == "name":

        if "name" in clean_words:

            start = clean_words.index("name") + 1
            name_confidences = []

            for j in range(start, len(words)):

                if clean_words[j] in [
                    "date",
                    "document"
                ]:
                    break

                name_confidences.append(confidences[j])

            if name_confidences:

                return round(
                    sum(name_confidences)
                    / len(name_confidences),
                    2
                )

    # -------------------------
    # DOB CONFIDENCE
    # -------------------------

    elif field.lower() == "dob":

        for i in range(len(words) - 3):

            word1 = words[i].strip(":").lower()
            word2 = words[i + 1].strip(":").lower()
            word3 = words[i + 2].strip(":").lower()

            if (
                word1 == "date"
                and word2 == "of"
                and word3 == "birth"
            ):

                if i + 3 < len(confidences):

                    return round(
                        confidences[i + 3],
                        2
                    )

    return 0.0


# =========================================================
# DOCUMENT TYPE
# =========================================================

def detect_document_type(text):
    """Detect the likely document type."""

    text_upper = text.upper()

    if (
        "AADHAAR" in text_upper
        or "UNIQUE IDENTIFICATION" in text_upper
    ):
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

    return "Unknown"


# =========================================================
# DOB VALIDATION
# =========================================================

def validate_dob(dob):
    """Check whether the extracted DOB is a valid date."""

    if not dob:
        return False

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y"
    ]

    for date_format in formats:

        try:
            datetime.strptime(
                dob,
                date_format
            )

            return True

        except ValueError:
            continue

    return False


# =========================================================
# FIELD EXTRACTION
# =========================================================

def extract_fields(text):
    """Extract important fields from OCR text."""

    fields = {
        "name": None,
        "date_of_birth": None,
        "document_id": None
    }

    # -------------------------
    # Correct common OCR mistakes
    # -------------------------

    text = text.replace("Narne", "Name")
    text = text.replace("D0B", "DOB")
    text = text.replace("Docurnent", "Document")

    # -------------------------
    # NAME
    # -------------------------

    name_match = re.search(
        r"Name\s*[:\-]?\s*(.*?)"
        r"(?=\s+"
        r"(?:DOB|Date of Birth|Birth Date|Document ID)\b"
        r"|$)",
        text,
        re.IGNORECASE
    )

    if name_match:

        fields["name"] = (
            name_match
            .group(1)
            .strip()
        )

    # -------------------------
    # DATE OF BIRTH
    # -------------------------

    dob_match = re.search(
        r"(?:DOB|Date of Birth|Birth Date)"
        r"\s*[:\-]?\s*"
        r"([0-9O@IlS]{1,2}"
        r"\s*[/-]\s*"
        r"[0-9O@IlS]{1,2}"
        r"\s*[/-]\s*"
        r"[0-9O@IlS]{2,4})",
        text,
        re.IGNORECASE
    )

    if dob_match:

        dob = dob_match.group(1)

        # Common OCR corrections
        dob = dob.replace("@", "0")
        dob = dob.replace("O", "0")
        dob = dob.replace("I", "1")
        dob = dob.replace("l", "1")
        dob = dob.replace("\\", "")

        dob = re.sub(
            r"\s+",
            "",
            dob
        )

        fields["date_of_birth"] = dob

    # -------------------------
    # DOCUMENT ID
    # -------------------------

    id_match = re.search(
        r"(?:Document ID|Document Number|ID)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z0-9]+)",
        text,
        re.IGNORECASE
    )

    if id_match:

        fields["document_id"] = (
            id_match
            .group(1)
        )

    return fields


# =========================================================
# MAIN DOCUMENT PROCESSING FUNCTION
# =========================================================

def process_document(image_path):
    """
    Complete document screening pipeline.

    This function is used by both:
    1. The test program
    2. The web application
    """

    # -------------------------
    # Tampering analysis
    # -------------------------

    tamper_result = analyze_tampering(
        image_path
    )

    # -------------------------
    # OCR
    # -------------------------

    (
        text,
        ocr_confidence,
        words,
        confidences
    ) = extract_text(image_path)

    # -------------------------
    # Document type
    # -------------------------

    document_type = detect_document_type(
        text
    )

    # -------------------------
    # Extract fields
    # -------------------------

    fields = extract_fields(text)

    # -------------------------
    # Field confidence
    # -------------------------

    name_confidence = calculate_field_confidence(
        words,
        confidences,
        "name"
    )

    dob_confidence = calculate_field_confidence(
        words,
        confidences,
        "dob"
    )

    # -------------------------
    # Validation
    # -------------------------

    fields["dob_valid"] = validate_dob(
        fields["date_of_birth"]
    )

    fields["name_valid"] = bool(
        fields["name"]
        and len(fields["name"].strip()) >= 2
    )

    fields["document_id_valid"] = bool(
        fields["document_id"]
        and len(fields["document_id"].strip()) >= 5
    )

    # -------------------------
    # Confidence results
    # -------------------------

    fields["ocr_confidence"] = round(
        ocr_confidence,
        2
    )

    fields["name_confidence"] = (
        name_confidence
    )

    fields["dob_confidence"] = (
        dob_confidence
    )

    # -------------------------
    # Document type
    # -------------------------

    fields["document_type"] = (
        document_type
    )

    # -------------------------
    # Tampering
    # -------------------------

    fields["tampering"] = (
        tamper_result
    )

    # -------------------------
    # Risk assessment
    # -------------------------

    risk_result = calculate_risk_score(
        fields
    )

    fields["risk_assessment"] = (
        risk_result
    )

    return fields, text


# =========================================================
# TEST PROGRAM
# =========================================================

if __name__ == "__main__":

    image_path = "documents/test.png"

    fields, text = process_document(
        image_path
    )

    # -------------------------
    # RAW OCR
    # -------------------------

    print(
        "\n========== RAW OCR =========="
    )

    print(text)

    # -------------------------
    # OCR CONFIDENCE
    # -------------------------

    print(
        "\n========== OCR CONFIDENCE =========="
    )

    print(
        "Average OCR Confidence:",
        fields["ocr_confidence"],
        "%"
    )

    # -------------------------
    # DOCUMENT TYPE
    # -------------------------

    print(
        "\n========== DOCUMENT TYPE =========="
    )

    print(
        "Document Type:",
        fields["document_type"]
    )

    # -------------------------
    # TAMPERING
    # -------------------------

    print(
        "\n========== TAMPERING ANALYSIS =========="
    )

    print(
        "Status:",
        fields["tampering"]["status"]
    )

    print(
        "Tampering Score:",
        fields["tampering"]["tampering_score"]
    )

    print(
        "Signals:",
        fields["tampering"]["signals"]
    )

    # -------------------------
    # FIELD CONFIDENCE
    # -------------------------

    print(
        "\n========== FIELD CONFIDENCE =========="
    )

    print(
        "Name Confidence:",
        fields["name_confidence"]
    )

    print(
        "DOB Confidence:",
        fields["dob_confidence"]
    )

    # -------------------------
    # EXTRACTED FIELDS
    # -------------------------

    print(
        "\n========== EXTRACTED FIELDS =========="
    )

    print(
        "Name:",
        fields["name"]
    )

    print(
        "Date of Birth:",
        fields["date_of_birth"]
    )

    print(
        "Document ID:",
        fields["document_id"]
    )

    print(
        "DOB Valid:",
        fields["dob_valid"]
    )

    print(
        "Name Valid:",
        fields["name_valid"]
    )

    print(
        "Document ID Valid:",
        fields["document_id_valid"]
    )

    # -------------------------
    # RISK ASSESSMENT
    # -------------------------

    print(
        "\n========== RISK ASSESSMENT =========="
    )

    print(
        "Risk Score:",
        fields["risk_assessment"]["risk_score"]
    )

    print(
        "Risk Category:",
        fields["risk_assessment"]["risk_category"]
    )

    print("Reasons:")

    for reason in fields[
        "risk_assessment"
    ]["reasons"]:

        print("-", reason)

    # -------------------------
    # SAVE JSON
    # -------------------------

    with open(
        "ocr_result.json",
        "w"
    ) as file:

        json.dump(
            fields,
            file,
            indent=4
        )

    print(
        "\nOCR result saved to ocr_result.json"
    )