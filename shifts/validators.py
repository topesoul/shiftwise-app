# /workspace/shiftwise/shifts/validators.py

from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions


def validate_image(file):
    """
    Validates that the uploaded file is a valid image and within size constraints.

    Args:
        file (File): The uploaded file to validate.

    Raises:
        ValidationError: If the file is not a valid image or exceeds the size limit.
    """
    try:
        # Attempt to get image dimensions to verify it's a valid image
        w, h = get_image_dimensions(file)
    except Exception:
        # If an exception occurs, the file is not a valid image
        raise ValidationError("Uploaded file is not a valid image.")

    # Enforce maximum file size of 2MB
    max_size = 2 * 1024 * 1024  # 2MB in bytes
    if file.size > max_size:
        raise ValidationError("Image file too large ( > 2MB ).")
