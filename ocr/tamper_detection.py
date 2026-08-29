from PIL import Image, ImageChops, ImageEnhance
import os


def analyze_tampering(image_path):
    """
    Perform basic image-level tampering checks.

    This is an initial screening signal, not proof that a
    document is genuine or fake.
    """

    result = {
        "tampering_score": 0.0,
        "status": "No obvious tampering detected",
        "signals": []
    }

    # Check whether the file exists
    if not os.path.exists(image_path):
        result["status"] = "Image not found"
        result["signals"].append("Input image does not exist")
        return result

    try:
        image = Image.open(image_path)

        # Check image dimensions
        width, height = image.size

        if width < 500 or height < 300:
            result["signals"].append(
                "Low image resolution"
            )
            result["tampering_score"] += 0.15

        # Check whether the image contains EXIF metadata
        exif_data = image.getexif()

        if not exif_data:
            result["signals"].append(
                "No EXIF metadata found"
            )

        # Basic image consistency check
        gray = image.convert("L")

        enhanced = ImageEnhance.Contrast(gray).enhance(2)

        difference = ImageChops.difference(
            gray,
            enhanced
        )

        bbox = difference.getbbox()

        if bbox is not None:
            result["signals"].append(
                "Image contrast variation detected"
            )

        # Limit score between 0 and 1
        result["tampering_score"] = min(
            result["tampering_score"],
            1.0
        )

        # Determine status
        if result["tampering_score"] >= 0.5:
            result["status"] = "Potential tampering detected"

        return result

    except Exception as e:

        result["status"] = "Analysis failed"

        result["signals"].append(str(e))

        return result