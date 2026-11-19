# Health Prediction App

A small patient records app. Each record holds a patient's details and three blood test values, and the Google Gemini API writes a short remark about a possible health condition or risk.

Built with Python, Streamlit (interface), SQLite (storage) and the Google Gemini API (remarks).

> Remarks are screening estimates from an AI model. They are not medical diagnoses.

---

## What it does

- **Create, read, update and delete** patient records
- **Validates** every field before saving (see the table below)
- **Stores** records in a local SQLite database (`patients.db`, created on first run)
- **Calls the Gemini API** after valid data is entered and saves the result in the Remarks column

Each record stores: full name, date of birth, email, glucose, haemoglobin, cholesterol and remarks.

---

## Setup

You need Python 3.10 or newer and a free Gemini API key from https://aistudio.google.com (sign in with a Google account, then choose Get API key).

```bash
# 1. Install the libraries
python -m pip install -r requirements.txt

# 2. Create your .env file from the example, then open it and paste your key
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

# 3. Run the app
python -m streamlit run app.py
```

The app opens at http://localhost:8501. If that port is busy, add `--server.port 8502`.

If the key is missing or the API call fails, the record is still saved with the remark "AI remark unavailable (...)". There are no automatic retries, so the free quota is never used twice for one save. The remark is requested again only when you click **Update patient** on that record.

---

## Project structure

```
health-prediction-app/
├── app.py              # Streamlit interface (three tabs)
├── database.py         # SQLite: table creation, CRUD, duplicate check
├── validators.py       # Input validation rules
├── ai_remarks.py       # Gemini API call
├── tests/
│   └── test_records.py # Runs the 10 assignment records through validation
├── requirements.txt
├── .env.example        # Template for the API key (the real .env is git-ignored)
└── .gitignore
```

Each file has one job. `app.py` only draws the screen and calls the other three.

---

## How it works

**Adding a patient**

1. The form values arrive as text.
2. `validate_patient()` checks all six fields and returns every error at once.
3. `find_duplicate()` checks the database for the same email, or the same name and date of birth.
4. If everything passes, `get_remarks()` calls Gemini.
5. The record and the remark are saved with `add_patient()`.

**Editing a patient.** The same checks run, and the record itself is excluded from the duplicate check. A new AI remark is requested only if the date of birth or a blood value changed (or the previous remark failed). Changing just the email keeps the existing remark.

**AI integration (`ai_remarks.py`).** The prompt contains only the patient's age and the three blood values. Name and email are never sent. Gemini is asked for one or two short sentences naming the most likely condition or risk. The API key is read from the `.env` file and is never written in the code. Exactly one API call is made per save, with no automatic retries and no fallback model. If that call fails, the record is still saved and the Remarks column shows the reason, for example "Gemini is busy" (HTTP 503) or "free quota used up" (HTTP 429). The thinking level is set to `low` by default (`GEMINI_THINKING_LEVEL`) to keep responses quick. Google's free tier may use requests to improve its products, which is one reason no personal details are sent.

---

## Validation rules

| Field | Rule |
|---|---|
| Full name | Required. Letters, spaces, dots, hyphens and apostrophes only |
| Date of birth | Must be dd/mm/yyyy (dd.mm.yyyy is also accepted and converted), must be a real calendar date, cannot be in the future, not before 1900 |
| Email | Must look like `name@domain.com` |
| Glucose | A number from 20 to 1000 (mg/dL) |
| Haemoglobin | A number from 3 to 25 (g/dL) |
| Cholesterol | A number from 50 to 1000 (mg/dL) |
| Duplicates | Rejected if the email already exists, or the name and date of birth already exist |

The numeric fields are text boxes on purpose, so that non-numeric input is caught by the validation code and shown as an error.

---

## Test data results

The assignment's 10 test records, entered exactly as given. Run `python tests/test_records.py` to reproduce this without the AI call.

| # | Name | Result | Reason |
|---|---|---|---|
| 1 | Robyn Pears | Saved | |
| 2 | John Hunter | **Rejected** | Email `hunter@gmail` has no domain ending such as `.com` |
| 3 | Darryl Tim | Saved | |
| 4 | Peter Larry | **Rejected** | 31/11/2001 does not exist, because November has 30 days |
| 5 | Sam Kerr | Saved | |
| 6 | Robyn Pears | **Rejected** | Duplicate of record 1 (same email, same name and date of birth) |
| 7 | Madison XI | Saved | The name contains only letters, so it is valid |
| 8 | Kris Wu | **Rejected** | Two errors: date of birth 19/10/2030 is in the future, and `Kris.wu.gmail.com` has no `@` |
| 9 | Tenille Singh | Saved | |
| 10 | Prem Kumar | Saved | |

In the assignment table, test 8's cholesterol and test 9's number run together ("1979"). The cholesterol value is 197.

---

## Limitations

- Validation ranges are broad sanity limits, not clinical reference ranges.
- Sex is not collected, so the AI uses general adult ranges.
- Remarks depend on the AI model and can vary between runs.
- Single-user app with no login. SQLite is suited to this size, not to many users at once.
- No automated test covers the live Gemini call, because it needs a real API key.
- The free Gemini tier has a small daily request limit per model, so a heavy testing day can exhaust it.
