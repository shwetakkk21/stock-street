# app.py
import streamlit as st
import pandas as pd
from src.auth import render_login_screen, render_sidebar_profile
from src.data_manager import fetch_sheet_payload, process_and_coerce_df
from src.analytics import render_temporal_analysis, render_distribution_plots

st.set_page_config(page_title="Stock Street", layout="wide", page_icon="📈")

# Validate environment config blocks
if "auth" not in st.secrets:
    st.error("Missing authentication config secrets configuration.")
    st.stop()

# Gateway Auth Checks
if not st.user.is_logged_in:
    render_login_screen()

render_sidebar_profile()

# Mount Target Input Document Resource Handles
from src.database import get_user_sheet, save_user_sheet, delete_user_sheet

# Handle Sheet Existence
if "active_sheet_url" not in st.session_state:
    st.session_state["active_sheet_url"] = ""

# Fetch from FireBase
if st.session_state["active_sheet_url"] == "" and st.user.is_logged_in:
    user_email = st.user.email
    st.session_state["active_sheet_url"] = get_user_sheet(user_email)

# Sidebar
st.sidebar.subheader("Target Data Source")

if st.session_state["active_sheet_url"] == "":
    input_url = st.sidebar.text_input(
        "Google Sheet URL", 
        value="",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Paste the full link of a sheet you have access to modify."
    )
    
    if input_url:
        st.session_state["active_sheet_url"] = input_url
        
        # Commit permanently to the database under user's account name
        if st.user.is_logged_in:
            save_user_sheet(st.user.email, input_url)
            
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.success("Sheet Data Stream Connected!")
    
    display_url = st.session_state["active_sheet_url"]
    shortened_url = display_url[:30] + "..." if len(display_url) > 30 else display_url
    st.sidebar.text_input("Active Workspace URL", value=shortened_url, disabled=True)
    
    # Unlink
    if st.sidebar.button("🗑️ Unlink Current Sheet", type="secondary", width="stretch"):
        # 1. Clear out local memory states
        st.session_state["active_sheet_url"] = ""
        
        # 2. Wipe the link relationship from the cloud database database profile
        if st.user.is_logged_in:
            delete_user_sheet(st.user.email)
            
        st.cache_data.clear()
        st.sidebar.warning("Data link broken.")
        st.rerun()

# ----------------- STREAM INTEGRATION -----------------
if st.session_state["active_sheet_url"] == "":
    st.info("Welcome to Stock Street! Please paste a target Google Sheet URL in the sidebar workspace configuration panel to map your stock journal.")
    st.stop()

sheet_url = st.session_state["active_sheet_url"]
worksheet, raw_df = fetch_sheet_payload(sheet_url)

if raw_df is None or raw_df.empty:
    st.warning("Empty data grid returned. Ensure your column templates match expected criteria fields.")
    st.stop()

# Clean dataframe layout pipeline mapping
df = process_and_coerce_df(raw_df)

# 4. Global High-Level Summary Metrics View
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tracked Assets", len(df))
m2.metric("Portfolio Max Position", f"₹ {df['Price'].max():,.2f}")

st.write("---")

tab1, tab2, tab3 = st.tabs(["Live Explorer & Sync Engine", "Advanced Trend Analysis", "Asset Controls"])

# Tab 1

with tab1:
    st.subheader("Live Data Editor")
    st.caption("Double-click any cell below to edit it. Changes will write back to Google Sheets when you click 'Save Changes'.")
    
    edited_df = st.data_editor(df, num_rows="dynamic", width="stretch", key="prod_editor_grid")
    
    if st.button("Save Changes & Sync Sheet", type="primary"):
        try:
            # Format your structural list payload matching your sheet layout
            updated_data = [edited_df.columns.tolist()] + edited_df.values.tolist()
            
            # Extract the raw, un-wrapped authorization token string and metadata
            auth_token = worksheet.client.auth.token if hasattr(worksheet.client.auth, 'token') else worksheet.client.auth.access_token
            spreadsheet_id = worksheet.spreadsheet.id
            sheet_name = worksheet.title
            
            import requests
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }

            # This replaces the native worksheet.clear() method via a raw REST API POST call
            clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A2:Z:clear"
            clear_response = requests.post(clear_url, headers=headers)
            
            if clear_response.status_code != 200:
                st.error(f"Google Clear Gateway Rejected Request: {clear_response.text}")
                st.stop()

            # Write the new data matrix back starting at A2 via a raw REST API PUT call
            # Keep the URL range specific to the starting block cell coordinate
            update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A2"
            params = {"valueInputOption": "USER_ENTERED"}
            
            # Ensure the JSON body range matches the URL block string perfectly
            payload = {
                "range": f"{sheet_name}!A2",
                "majorDimension": "ROWS",
                "values": updated_data
            }
            
            update_response = requests.put(update_url, headers=headers, params=params, json=payload)
            
            if update_response.status_code == 200:
                st.success("Live Sheet successfully updated and synchronized via pure REST API!")
                st.cache_data.clear()  # Clear the 60-second cache memory instantly
                st.rerun()
            else:
                st.error(f"Google Update Gateway Rejected Request: {update_response.text}")
                
        except Exception as e:
            st.error(f"Failed to update sheet due to application error: {e}")

# TAB 2: DATA ANALYSIS CHANNELS


# TAB 3: ASSET CREATION & DELETION INTERFACES
with tab3:
    with st.expander("➕ Append Isolated Portfolio Position"):
        with st.form("add_form", clear_on_submit=True):
            tick = st.text_input("Asset Ticker Symbol").upper()
            c_name = st.text_input("Corporate Entity Identity Reference")
            status_val = st.selectbox("Status", ["Watchlist", "Owned", "Target reached"])
            prc = st.number_input("Price ($)", min_value=0.0, format="%.2f")
            pe_val = st.number_input("P/E Ratio", min_value=0.0, format="%.2f")
            vol_val = st.number_input("Base Allocation Volume", min_value=0, step=1)
            
            if st.form_submit_button("Execute Append Instruction"):
                if tick and c_name:
                    ts_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    worksheet.append_row([tick, c_name, prc, pe_val, vol_val, status_val, ts_str])
                    st.success(f"Position instance {tick} successfully registered.")
                    st.cache_data.clear()
                    st.rerun()

    with st.expander("🗑️ Destructive Entry Purging"):
        target_ticker = st.selectbox("Select Asset Entry to Purge", [""] + df['Symbol'].unique().tolist())
        if st.button("Confirm Explicit Deletion", type="primary") and target_ticker:
            cell = worksheet.find(target_ticker)
            if cell:
                worksheet.delete_rows(cell.row)
                st.success(f"Row containing record identification signature {target_ticker} removed.")
                st.cache_data.clear()
                st.rerun()