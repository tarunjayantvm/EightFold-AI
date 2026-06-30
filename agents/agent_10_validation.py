import re

def validate(profile: dict) -> dict:
    """
    Agent 10 — Validation Agent
    Validates the final output profile.
    Returns the profile with a validation report.
    Never crashes — always returns something.
    """
    errors   = []
    warnings = []

    # Required field checks
    if not profile.get("full_name"):
        errors.append("full_name is missing or empty.")

    # Email format
    for email in profile.get("emails") or []:
        if email and not re.match(r"^[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", str(email)):
            errors.append(f"Invalid email format: {email}")

    # Phone format — must be E.164
    for phone in profile.get("phones") or []:
        if phone and not re.match(r"^\+\d{7,15}$", str(phone)):
            errors.append(f"Phone not in E.164 format: {phone}")

    # Education date format
    for edu in profile.get("education") or []:
        if isinstance(edu, dict):
            end = edu.get("end_year")
            if end and not re.match(r"^\d{4}-\d{2}$", str(end)):
                warnings.append(f"Education end_year not YYYY-MM: {end}")

    # Confidence range check
    conf = profile.get("overall_confidence")
    if conf is not None and not (0.0 <= conf <= 1.0):
        errors.append(f"overall_confidence out of range: {conf}")

    # Structured collections should be lists
    for key in ["education", "experience", "projects", "certifications"]:
        value = profile.get(key)
        if value is None:
            profile[key] = []
        elif not isinstance(value, list):
            warnings.append(f"{key} should be a list")
            profile[key] = []

    # Location country ISO check
    loc     = profile.get("location") or {}
    country = loc.get("country") if isinstance(loc, dict) else None
    if country and not re.match(r"^[A-Z]{2}$", str(country)):
        warnings.append(f"Country may not be ISO alpha-2: {country}")

    profile["_validation"] = {
        "passed":   len(errors) == 0,
        "errors":   errors,
        "warnings": warnings
    }

    return profile