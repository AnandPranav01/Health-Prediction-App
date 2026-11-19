"""
tests/test_records.py
Runs the 10 test records from the assignment through validation and the
duplicate check, using a temporary database (patients.db is not touched).
No AI call is made here.

Run with:  python tests/test_records.py
"""

import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from validators import validate_patient

# Values are typed exactly as in the assignment table.
# Test 8: cholesterol is 197 (the "9" after it is the number of test 9).
TEST_RECORDS = [
    (1, "Robyn Pears", "28.01.1960", "robyn@gmail.com", "232", "13.5", "180"),
    (2, "John Hunter", "10.12.1990", "hunter@gmail", "94", "15", "200"),
    (3, "Darryl Tim", "12.11.1993", "timd@smh.com.au", "240", "18.6", "326"),
    (4, "Peter Larry", "31.11.2001", "Larry@hotmail.com", "88", "11.5", "165"),
    (5, "Sam Kerr", "09.12.2006", "sam@news.com.au", "198", "8.9", "192"),
    (6, "Robyn Pears", "28.01.1960", "robyn@gmail.com", "232", "13.5", "180"),
    (7, "Madison XI", "12.09.1998", "madison@hotmail.com", "85", "7.6", "163"),
    (8, "Kris Wu", "19.10.2030", "Kris.wu.gmail.com", "79", "16.5", "197"),
    (9, "Tenille Singh", "30.11.1991", "Tenille@yahoo.com", "101", "15", "310"),
    (10, "Prem Kumar", "28.04.1990", "prem@telstra.com", "155", "12.5", "265"),
]

EXPECTED_SAVED = {1, 3, 5, 7, 9, 10}
EXPECTED_REJECTED = {2, 4, 6, 8}


def main():
    database.DB_FILE = os.path.join(tempfile.mkdtemp(), "test.db")
    database.init_db()

    saved, rejected = set(), set()
    for number, name, dob, email, glucose, hb, chol in TEST_RECORDS:
        clean, errors = validate_patient(name, dob, email, glucose, hb, chol)
        if not errors:
            duplicate = database.find_duplicate(
                clean["full_name"], clean["date_of_birth"], clean["email"]
            )
            if duplicate:
                errors.append(duplicate)

        if errors:
            rejected.add(number)
            print(f"Test {number:>2} {name:<14} REJECTED")
            for message in errors:
                print(f"           - {message}")
        else:
            clean["remarks"] = "test"
            database.add_patient(clean)
            saved.add(number)
            print(f"Test {number:>2} {name:<14} saved")

    assert saved == EXPECTED_SAVED, f"saved {sorted(saved)}"
    assert rejected == EXPECTED_REJECTED, f"rejected {sorted(rejected)}"
    assert len(database.get_all_patients()) == len(EXPECTED_SAVED)
    print("\nAll checks passed: 6 saved, 4 rejected.")


if __name__ == "__main__":
    main()
