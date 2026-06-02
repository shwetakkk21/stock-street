# src/data_manager.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.credentials import Credentials

@st.cache_data(ttl=60)
def fetch_sheet_payload(sheet_url):
    """
    Establishes connection context and reads raw worksheet rows, 
    matching the exact row indexing architecture of app1.py.
    """
    try:
        # --- PATH A: PRODUCTION CLOUD HANDSHAKE ---
        if st.user and "token" in st.user:
            user_access_token = st.user["token"]
            creds = Credentials(
                token=user_access_token,
                client_id=st.secrets["auth"]["client_id"],
                client_secret=st.secrets["auth"]["client_secret"],
            )
            gc = gspread.authorize(creds)
            
        # --- PATH B: LOCAL DEVELOPMENT FALLBACK ---
        elif "gspread_local" in st.secrets:
            cred_dict = dict(st.secrets["gspread_local"])
            gc = gspread.service_account_from_dict(cred_dict)
            
        else:
            st.error("Missing valid execution context or local gspread credentials configuration.")
            return None, None

        sh = gc.open_by_url(sheet_url)
        worksheet = sh.get_worksheet(0)
        
        # Grab raw structural value lists
        raw_data = worksheet.get_all_values()
        if not raw_data or len(raw_data) < 2:
            return worksheet, pd.DataFrame()
            
        # MATCHING APP1.PY: Headers live on Row 2 (Index 1), Data from Row 3 (Index 2)
        headers = raw_data[1]
        rows = raw_data[2:]
        
        # --- APP1.PY CLEANED HEADER ENGINE ---
        cleaned_headers = []
        seen_headers = {}
        
        for i, h in enumerate(headers):
            h_stripped = h.strip()
            
            # If the header is completely blank, give it a placeholder name
            if h_stripped == "":
                h_stripped = f"Unnamed_{i}"
                
            # If we have seen this column name before, make it unique
            if h_stripped in seen_headers:
                seen_headers[h_stripped] += 1
                h_stripped = f"{h_stripped}_{seen_headers[h_stripped]}"
            else:
                seen_headers[h_stripped] = 0
                
            cleaned_headers.append(h_stripped)
            
        df = pd.DataFrame(rows, columns=cleaned_headers)
        
        # Filter out columns that were completely empty in the Google Sheet
        df = df.loc[:, ~df.columns.str.startswith('Unnamed_')]
        
        return worksheet, df
        
    except Exception as e:
        st.error(f"Google Sheet Connection Refused: {e}")
        return None, None

def process_and_coerce_df(df):
    """
    Enforces precise numeric conversion rules and fallback defaults 
    exactly as configured in app1.py.
    """
    if df.empty:
        return df
        
    # Convert numeric columns from strings to actual numbers safely
    numeric_cols = ['Price', 'PE Ratio', 'Volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Fill empty/broken numeric values so math functions don't break
    if 'Price' in df.columns: 
        df['Price'] = df['Price'].fillna(0.0)
    if 'PE Ratio' in df.columns: 
        df['PE Ratio'] = df['PE Ratio'].fillna(0.0)
    if 'Volume' in df.columns: 
        df['Volume'] = df['Volume'].fillna(0).astype(int)
        
    # Ensure standard Timestamp mapping behaves nicely if available
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        
    return df