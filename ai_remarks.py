

import os
from datetime import date, datetime

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()  # reads GEMINI_API_KEY from the .env file

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# How hard the model thinks before answering: "low" is faster.
# Leave empty to use the model's own default.
THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "low")
UNAVAILABLE = "AI remark unavailable"

PROMPT = """You are helping a health screening tool. Using the age and blood test \
results below, name the single most likely health condition or risk (for example \
diabetes, pre-diabetes, anaemia, high cholesterol, or no significant risk).

Patient age: {age} years (sex not provided, use general adult ranges)
Glucose: {glucose} mg/dL
Haemoglobin: {haemoglobin} g/dL
Total cholesterol: {cholesterol} mg/dL

Reply with the remark only: one or two short sentences, at most 40 words. \
Start with "Possible" or "Low risk". This is a screening estimate, not a diagnosis."""


def calculate_age(dob_text):
    born = datetime.strptime(dob_text, "%d/%m/%Y").date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def remark_failed(remark):
    """True if the saved remark is empty or is an error message."""
    return not remark or remark.startswith(UNAVAILABLE)


def build_config():
    """Ask for a lower thinking level so the answer comes back faster."""
    if not THINKING_LEVEL:
        return None
    return types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL)
    )


def get_remarks(dob_text, glucose, haemoglobin, cholesterol):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return f"{UNAVAILABLE} (GEMINI_API_KEY is not set)."

    prompt = PROMPT.format(
        age=calculate_age(dob_text),
        glucose=glucose,
        haemoglobin=haemoglobin,
        cholesterol=cholesterol,
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL, contents=prompt, config=build_config()
        )
        text = (response.text or "").strip()
        if not text:
            return f"{UNAVAILABLE} (empty response)."
        return text
    except errors.APIError as error:
        print(f"Gemini API error: {error}")  # full detail goes to the terminal only
        if error.code == 503:
            reason = "Gemini is busy, use Update patient to try again"
        elif error.code == 429:
            reason = "free quota used up"
        else:
            reason = type(error).__name__
        return f"{UNAVAILABLE} ({reason})."
    except Exception as error:
        print(f"Gemini error: {error}")
        return f"{UNAVAILABLE} ({type(error).__name__})."
