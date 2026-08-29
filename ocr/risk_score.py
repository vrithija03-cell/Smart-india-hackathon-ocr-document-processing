def calculate_risk_score(data):
    """
    Calculate a document risk score from 0 to 100.

    Higher score = higher risk.
    """

    risk_score = 0
    reasons = []

    # 1. Overall OCR confidence
    ocr_confidence = data.get("ocr_confidence", 0)

    if ocr_confidence < 50:
        risk_score += 25
        reasons.append("Very low OCR confidence")

    elif ocr_confidence < 75:
        risk_score += 15
        reasons.append("Low OCR confidence")

    # 2. Name confidence
    name_confidence = data.get("name_confidence", 0)

    if name_confidence < 50:
        risk_score += 15
        reasons.append("Low name recognition confidence")

    elif name_confidence < 75:
        risk_score += 8
        reasons.append("Moderate name recognition confidence")

    # 3. DOB confidence
    dob_confidence = data.get("dob_confidence", 0)

    if dob_confidence < 50:
        risk_score += 15
        reasons.append("Low date-of-birth recognition confidence")

    elif dob_confidence < 75:
        risk_score += 8
        reasons.append("Moderate date-of-birth recognition confidence")

    # 4. Field validation
    if not data.get("name_valid", False):
        risk_score += 15
        reasons.append("Name field is invalid")

    if not data.get("dob_valid", False):
        risk_score += 15
        reasons.append("Date of birth is invalid")

    if not data.get("document_id_valid", False):
        risk_score += 15
        reasons.append("Document ID is invalid")

    # 5. Tampering evidence
    tampering = data.get("tampering", {})

    tampering_score = tampering.get(
        "tampering_score", 0
    )

    if tampering_score >= 0.5:
        risk_score += 30
        reasons.append("Potential image tampering detected")

    elif tampering_score >= 0.25:
        risk_score += 15
        reasons.append("Some image tampering indicators detected")

    # Keep score between 0 and 100
    risk_score = min(risk_score, 100)

    # Risk category
    if risk_score >= 60:
        category = "HIGH RISK"

    elif risk_score >= 30:
        category = "MEDIUM RISK"

    else:
        category = "LOW RISK"

    return {
        "risk_score": risk_score,
        "risk_category": category,
        "reasons": reasons
    }
if __name__ == "__main__":

    test_data = {
        "ocr_confidence": 80.2,
        "name_confidence": 96.0,
        "dob_confidence": 22.0,
        "name_valid": True,
        "dob_valid": True,
        "document_id_valid": True,
        "tampering": {
            "tampering_score": 0.0
        }
    }

    result = calculate_risk_score(test_data)

    print("\n========== RISK ASSESSMENT ==========")
    print("Risk Score:", result["risk_score"])
    print("Risk Category:", result["risk_category"])

    print("\nReasons:")
    for reason in result["reasons"]:
        print("-", reason)