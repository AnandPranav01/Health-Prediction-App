

import sqlite3

import pandas as pd
import streamlit as st

import database
from ai_remarks import get_remarks, remark_failed
from validators import validate_patient

st.set_page_config(page_title="Health Prediction App", page_icon="🩺", layout="wide")
database.init_db()


if "form_id" not in st.session_state:
    st.session_state.form_id = 0
if "flash" not in st.session_state:
    st.session_state.flash = None


def check_patient(name, dob, email, glucose, haemoglobin, cholesterol, exclude_id=None):
    """Validate the fields, then check for duplicates. Returns (clean, errors)."""
    clean, errors = validate_patient(name, dob, email, glucose, haemoglobin, cholesterol)
    if not errors:
        duplicate = database.find_duplicate(
            clean["full_name"], clean["date_of_birth"], clean["email"], exclude_id
        )
        if duplicate:
            errors.append(duplicate)
    return clean, errors


def make_remarks(clean):
    with st.spinner("Asking the AI for health remarks..."):
        return get_remarks(
            clean["date_of_birth"],
            clean["glucose"],
            clean["haemoglobin"],
            clean["cholesterol"],
        )


def show_errors(errors):
    for message in errors:
        st.error(message)


def number_text(value):
    """232.0 -> '232', 13.5 -> '13.5'"""
    return f"{value:g}"


st.title("Health Prediction App")
st.caption(
    "Patient blood test records with AI-generated remarks. "
    "Remarks are screening estimates, not medical diagnoses."
)

if st.session_state.flash:
    st.success(st.session_state.flash)
    st.session_state.flash = None

tab_add, tab_list, tab_edit = st.tabs(["Add patient", "All records", "Edit or delete"])

# ---------------------------------------------------------------- Add patient
with tab_add:
    fid = st.session_state.form_id
    with st.form(f"add_form_{fid}"):
        name = st.text_input("Full name", key=f"add_name_{fid}")
        dob = st.text_input("Date of birth (dd/mm/yyyy)", key=f"add_dob_{fid}")
        email = st.text_input("Email address", key=f"add_email_{fid}")
        col1, col2, col3 = st.columns(3)
        glucose = col1.text_input("Glucose (mg/dL)", key=f"add_glucose_{fid}")
        haemoglobin = col2.text_input("Haemoglobin (g/dL)", key=f"add_hb_{fid}")
        cholesterol = col3.text_input("Cholesterol (mg/dL)", key=f"add_chol_{fid}")
        save = st.form_submit_button("Save patient")

    if save:
        clean, errors = check_patient(name, dob, email, glucose, haemoglobin, cholesterol)
        if errors:
            show_errors(errors)
        else:
            clean["remarks"] = make_remarks(clean)
            try:
                database.add_patient(clean)
            except sqlite3.IntegrityError:
                st.error("This email already exists in the database.")
            else:
                message = f"Saved {clean['full_name']}."
                if remark_failed(clean["remarks"]):
                    message += " The AI remark could not be generated; it will be retried when you edit this record."
                st.session_state.flash = message
                st.session_state.form_id += 1
                st.rerun()

# ---------------------------------------------------------------- All records
with tab_list:
    patients = database.get_all_patients()
    st.subheader(f"All records ({len(patients)})")
    if not patients:
        st.info("No records yet. Add a patient in the first tab.")
    else:
        table = pd.DataFrame(patients).rename(
            columns={
                "id": "ID",
                "full_name": "Full name",
                "date_of_birth": "Date of birth",
                "email": "Email",
                "glucose": "Glucose",
                "haemoglobin": "Haemoglobin",
                "cholesterol": "Cholesterol",
                "remarks": "Remarks",
            }
        )
        st.table(table.set_index("ID"))

# ------------------------------------------------------------- Edit or delete
with tab_edit:
    patients = database.get_all_patients()
    if not patients:
        st.info("No records to edit yet.")
    else:
        labels = {p["id"]: f"{p['id']} - {p['full_name']} ({p['email']})" for p in patients}
        selected_id = st.selectbox(
            "Choose a patient", list(labels), format_func=lambda pid: labels[pid]
        )
        patient = database.get_patient(selected_id)
        sid = selected_id

        with st.form(f"edit_form_{sid}"):
            name = st.text_input("Full name", value=patient["full_name"], key=f"edit_name_{sid}")
            dob = st.text_input(
                "Date of birth (dd/mm/yyyy)", value=patient["date_of_birth"], key=f"edit_dob_{sid}"
            )
            email = st.text_input("Email address", value=patient["email"], key=f"edit_email_{sid}")
            col1, col2, col3 = st.columns(3)
            glucose = col1.text_input(
                "Glucose (mg/dL)", value=number_text(patient["glucose"]), key=f"edit_glucose_{sid}"
            )
            haemoglobin = col2.text_input(
                "Haemoglobin (g/dL)", value=number_text(patient["haemoglobin"]), key=f"edit_hb_{sid}"
            )
            cholesterol = col3.text_input(
                "Cholesterol (mg/dL)", value=number_text(patient["cholesterol"]), key=f"edit_chol_{sid}"
            )
            update = st.form_submit_button("Update patient")

        if update:
            clean, errors = check_patient(
                name, dob, email, glucose, haemoglobin, cholesterol, exclude_id=sid
            )
            if errors:
                show_errors(errors)
            else:
                health_data_changed = any(
                    clean[field] != patient[field]
                    for field in ("date_of_birth", "glucose", "haemoglobin", "cholesterol")
                )
                if health_data_changed or remark_failed(patient["remarks"]):
                    clean["remarks"] = make_remarks(clean)
                else:
                    clean["remarks"] = patient["remarks"]

                try:
                    database.update_patient(sid, clean)
                except sqlite3.IntegrityError:
                    st.error("This email already exists in the database.")
                else:
                    st.session_state.flash = f"Updated {clean['full_name']}."
                    st.rerun()

        st.divider()
        confirm = st.checkbox("Yes, delete this record", key=f"confirm_delete_{sid}")
        if st.button("Delete patient", disabled=not confirm):
            database.delete_patient(sid)
            st.session_state.flash = f"Deleted {patient['full_name']}."
            st.rerun()
