import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import json
from datetime import datetime

# Tesseract location
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def preprocess_image(image_path):
    """Improve the image before OCR."""
    image = Image.open(image_path)

    # Convert to grayscale
    image = image.convert("L")

    # Improve contrast
    image = ImageEnhance.Contrast(image).enhance(2)

    # Reduce small noise
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


def extract_text(image_path):
    """Extract text from the document image."""
    image = preprocess_image(image_path)

    text = pytesseract.image_to_string(image)

    return text


def validate_dob(dob):
    """Check whether the extracted DOB is a valid date."""

    if not dob:
        return False

    try:
        datetime.strptime(dob, "%d/%m/%Y")
        return True
    except ValueError:
        return False
def extract_fields(text):
    """Extract important fields from OCR text."""

    fields = {
        "name": None,
        "date_of_birth": None,
        "document_id": None
    }

    # Correct some common OCR mistakes
    text = text.replace("Narne", "Name")
    text = text.replace("D0B", "DOB")
    text = text.replace("Docurnent", "Document")

    # -------------------------
    # Find Name
    # -------------------------
    name_match = re.search(
        r"Name\s*[:\-]?\s*(.+)",
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

        # Correct OCR mistakes ONLY inside the DOB
        dob = dob.replace("@", "0")
        dob = dob.replace("O", "0")
        dob = dob.replace("I", "1")
        dob = dob.replace("l", "1")

        # Remove spaces
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


# -------------------------
# Main program
# -------------------------
if __name__ == "__main__":

    image_path = "documents/test.png"

    # Extract text
    text = extract_text(image_path)

    print("\n========== RAW OCR ==========")
    print(text)

    # Extract fields
    fields = extract_fields(text)

    # Validate DOB
    fields["dob_valid"] = validate_dob(fields["date_of_birth"])

    print("\n========== EXTRACTED FIELDS ==========")
    print("Name:", fields["name"])
    print("Date of Birth:", fields["date_of_birth"])
    print("Document ID:", fields["document_id"])
    print("DOB Valid:", fields["dob_valid"])

    # Save results as JSON
    with open("ocr_result.json", "w") as file:
        json.dump(fields, file, indent=4)

    print("\nOCR result saved to ocr_result.json")