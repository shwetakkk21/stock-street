# src/database.py
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

def get_db_client():
    """Initializes a Firestore client using your existing service account secrets."""
    # Works both locally and in production using your existing TOML layout
    cred_dict = dict(st.secrets["gspread_local"])
    creds = service_account.Credentials.from_service_account_info(cred_dict)
    return firestore.Client(credentials=creds, project=cred_dict["project_id"])

def get_user_sheet(email):
    """Looks up a persistent sheet link tied to a specific user email."""
    try:
        db = get_db_client()
        doc_ref = db.collection("user_workspaces").document(email)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("sheet_url", "")
    except Exception as e:
        st.sidebar.error(f"Database lookup failed: {e}")
    return ""

def save_user_sheet(email, sheet_url):
    """Saves or updates a persistent sheet link for a user."""
    try:
        db = get_db_client()
        doc_ref = db.collection("user_workspaces").document(email)
        doc_ref.set({"sheet_url": sheet_url, "updated_at": firestore.SERVER_TIMESTAMP})
    except Exception as e:
        st.sidebar.error(f"Database save failed: {e}")

def delete_user_sheet(email):
    """Removes the persistent sheet association from the database."""
    try:
        db = get_db_client()
        doc_ref = db.collection("user_workspaces").document(email)
        doc_ref.delete()
    except Exception as e:
        st.sidebar.error(f"Database deletion failed: {e}")