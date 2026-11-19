
import math
import re
from datetime import date, datetime

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]*$")
DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


GLUCOSE_RANGE = ("Glucose", 20, 1000)           # mg/dL
HAEMOGLOBIN_RANGE = ("Haemoglobin", 3, 25)      # g/dL
CHOLESTEROL_RANGE = ("Cholesterol", 50, 1000)   # mg/dL


def check_name(name):
    name = name.strip()
    if not name:
        return None, "Full name is required."
    if not NAME_PATTERN.match(name):
        return None, "Full name can only contain letters, spaces, dots, hyphens and apostrophes."
    return name, None


def check_email(email):
    email = email.strip()
    if not email:
        return None, "Email address is required."
    if not EMAIL_PATTERN.match(email):
        return None, f"'{email}' is not a valid email address (expected name@domain.com)."
    return email.lower(), None


def check_dob(text):
    """Accepts dd/mm/yyyy or dd.mm.yyyy and returns it as dd/mm/yyyy."""
    text = text.strip().replace(".", "/")
    if not text:
        return None, "Date of birth is required."
    if not DATE_PATTERN.match(text):
        return None, "Date of birth must be in dd/mm/yyyy format."
    try:
        dob = datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None, f"{text} is not a real calendar date."
    if dob > date.today():
        return None, "Date of birth cannot be in the future."
    if dob.year < 1900:
        return None, "Date of birth cannot be before 1900."
    return text, None


def check_number(text, label_min_max):
    label, minimum, maximum = label_min_max
    try:
        value = float(text.strip())
    except ValueError:
        return None, f"{label} must be a number."
    if not math.isfinite(value):
        return None, f"{label} must be a number."
    if not minimum <= value <= maximum:
        return None, f"{label} must be between {minimum} and {maximum}."
    return value, None


def validate_patient(name, dob, email, glucose, haemoglobin, cholesterol):
    """Return (clean_data, errors). clean_data is only complete if errors is empty."""
    checks = [
        ("full_name", check_name(name)),
        ("date_of_birth", check_dob(dob)),
        ("email", check_email(email)),
        ("glucose", check_number(glucose, GLUCOSE_RANGE)),
        ("haemoglobin", check_number(haemoglobin, HAEMOGLOBIN_RANGE)),
        ("cholesterol", check_number(cholesterol, CHOLESTEROL_RANGE)),
    ]

    clean = {}
    errors = []
    for field, (value, error) in checks:
        if error:
            errors.append(error)
        else:
            clean[field] = value
    return clean, errors
