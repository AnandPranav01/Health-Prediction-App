
database.py
All SQLite code lives here. The rest of the app never writes SQL directly.
"""

import sqlite3

DB_FILE = "patients.db"


def run(query, params=(), fetch=False):
    """Open the database, run one query, and close it again."""
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute(query, params)
        connection.commit()
        if fetch:
            return [dict(row) for row in cursor.fetchall()]
        return cursor.lastrowid
    finally:
        connection.close()


def init_db():
    """Create the patients table on first run."""
    run(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
            glucose       REAL NOT NULL,
            haemoglobin   REAL NOT NULL,
            cholesterol   REAL NOT NULL,
            remarks       TEXT
        )
        """
    )


# ---------- Create ----------
def add_patient(data):
    return run(
        """
        INSERT INTO patients
            (full_name, date_of_birth, email, glucose, haemoglobin, cholesterol, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["full_name"],
            data["date_of_birth"],
            data["email"],
            data["glucose"],
            data["haemoglobin"],
            data["cholesterol"],
            data["remarks"],
        ),
    )


# ---------- Read ----------
def get_all_patients():
    return run("SELECT * FROM patients ORDER BY id", fetch=True)


def get_patient(patient_id):
    rows = run("SELECT * FROM patients WHERE id = ?", (patient_id,), fetch=True)
    return rows[0] if rows else None


# ---------- Update ----------
def update_patient(patient_id, data):
    run(
        """
        UPDATE patients
        SET full_name = ?, date_of_birth = ?, email = ?,
            glucose = ?, haemoglobin = ?, cholesterol = ?, remarks = ?
        WHERE id = ?
        """,
        (
            data["full_name"],
            data["date_of_birth"],
            data["email"],
            data["glucose"],
            data["haemoglobin"],
            data["cholesterol"],
            data["remarks"],
            patient_id,
        ),
    )


# ---------- Delete ----------
def delete_patient(patient_id):
    run("DELETE FROM patients WHERE id = ?", (patient_id,))


# ---------- Duplicate check ----------
def find_duplicate(full_name, date_of_birth, email, exclude_id=None):
    """
    Return a message if another record has the same email, or the same
    name and date of birth. exclude_id lets a record be edited without
    clashing with itself.
    """
    other_id = exclude_id or 0

    same_email = run(
        "SELECT id FROM patients WHERE LOWER(email) = LOWER(?) AND id != ?",
        (email, other_id),
        fetch=True,
    )
    if same_email:
        return f"A patient with the email {email} already exists."

    same_person = run(
        """
        SELECT id FROM patients
        WHERE LOWER(full_name) = LOWER(?) AND date_of_birth = ? AND id != ?
        """,
        (full_name, date_of_birth, other_id),
        fetch=True,
    )
    if same_person:
        return f"{full_name} with date of birth {date_of_birth} already exists."

    return None
