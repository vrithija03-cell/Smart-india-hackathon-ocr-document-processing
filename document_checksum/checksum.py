# =========================================================
# ICAO 9303 DOCUMENT / MRZ CHECKSUM
# =========================================================

WEIGHTS = [7, 3, 1]


def character_value(char):
    """
    Convert an MRZ character to its ICAO 9303 value.

    0-9 -> 0-9
    A-Z -> 10-35
    <   -> 0
    """

    if char == "<":
        return 0

    if char.isdigit():
        return int(char)

    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10

    return 0


def calculate_check_digit(value):
    """
    Calculate the ICAO 9303 check digit.
    """

    total = 0

    for i, char in enumerate(value):
        total += character_value(char) * WEIGHTS[i % 3]

    return total % 10


def verify_check_digit(value, check_digit):
    """
    Verify a value against its check digit.
    """

    if not check_digit.isdigit():
        return False

    calculated = calculate_check_digit(value)

    return calculated == int(check_digit)


def validate_td3_mrz(line1, line2):
    """
    Validate important ICAO 9303 checks
    for a TD3 passport MRZ.
    """

    if len(line1) != 44 or len(line2) != 44:
        return {
            "valid": False,
            "error": "TD3 MRZ lines must contain 44 characters."
        }

    results = {}

    # Document number
    document_number = line2[0:9]
    document_number_check = line2[9]

    results["document_number"] = verify_check_digit(
        document_number,
        document_number_check
    )

    # Date of birth
    date_of_birth = line2[13:19]
    dob_check = line2[19]

    results["date_of_birth"] = verify_check_digit(
        date_of_birth,
        dob_check
    )

    # Expiry date
    expiry_date = line2[21:27]
    expiry_check = line2[27]

    results["expiry_date"] = verify_check_digit(
        expiry_date,
        expiry_check
    )

    # Overall check
    overall_data = (
        line2[0:10]
        + line2[13:20]
        + line2[21:43]
    )

    overall_check = line2[43]

    results["overall"] = verify_check_digit(
        overall_data,
        overall_check
    )

    results["valid"] = all(results.values())

    return results


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

    print("========== DOCUMENT CHECKSUM ==========")

    result = validate_td3_mrz(
        line1,
        line2
    )

    print(
        "Document Number:",
        "VALID" if result["document_number"] else "INVALID"
    )

    print(
        "Date of Birth:",
        "VALID" if result["date_of_birth"] else "INVALID"
    )

    print(
        "Expiry Date:",
        "VALID" if result["expiry_date"] else "INVALID"
    )

    print(
        "Overall Check:",
        "VALID" if result["overall"] else "INVALID"
    )

    print(
        "Overall MRZ:",
        "VALID" if result["valid"] else "INVALID"
    )