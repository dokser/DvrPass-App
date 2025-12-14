import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# --- Google Sheets Connection Setup ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "DVR_DB"  # Make sure this matches your Google Sheet name exactly

def get_connection():
    """Establishes connection to Google Sheets (Local & Cloud compatible)"""
    try:
        # Check if running on Streamlit Cloud (using Secrets)
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        
        # Check if running locally (using JSON file)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
            
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

def load_data():
    """Loads data from the cloud"""
    sheet = get_connection()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def add_to_sheet(brand, model, user, password, info):
    """Appends a new row to the cloud database"""
    sheet = get_connection()
    sheet.append_row([brand, model, user, password, info])

# --- App Interface (Global English) ---
st.set_page_config(page_title="Global DVR Hub", page_icon="🌍", layout="centered")

# Header & Introduction
st.title("🌍 Global DVR/NVR Password Hub")
st.markdown("""
**Welcome to the Open Database for Security Technicians.** This tool helps you find default passwords and reset methods for various DVR/NVR brands.  
**Community Driven:** If you find a new device, please add it to the database!
""")
st.divider()

# Load Data
try:
    df = load_data()
except Exception:
    df = pd.DataFrame(columns=["Brand", "Model", "User", "Pass", "Info"])

# Tabs
tab1, tab2 = st.tabs(["🔍 Search Device", "➕ Add / Contribute"])

# --- Tab 1: Search ---
with tab1:
    st.subheader("Find Password & Reset Info")
    
    if not df.empty:
        # Brand Selection
        brands = sorted(df['Brand'].astype(str).unique().tolist())
        selected_brand = st.selectbox("Select Brand / Manufacturer:", brands)
        
        if selected_brand:
            # Model Selection
            models = sorted(df[df['Brand'] == selected_brand]['Model'].astype(str).unique().tolist())
            selected_model = st.selectbox("Select Model / Series:", models)
            
            if selected_model:
                # Fetch Data
                try:
                    row = df[(df['Brand'] == selected_brand) & (df['Model'] == selected_model)].iloc[0]
                    
                    st.markdown("---")
                    # Display Credentials clearly
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Username:**\n\n{row['User']}")
                    with col2:
                        st.error(f"**Password:**\n\n{row['Pass']}")
                    
                    # Display Reset Instructions
                    st.warning(f"**Reset Instructions / Notes:**\n\n{row['Info']}")
                except IndexError:
                    st.error("Error fetching data for this model.")
    else:
        st.info("The database is currently empty or could not be loaded. Please verify the Google Sheet connection.")

# --- Tab 2: Add New Data ---
with tab2:
    st.subheader("Contribute to the Community 🤝")
    st.markdown("Found a device not in the list? Add it here to help technicians worldwide.")
    
    with st.form("add_form", clear_on_submit=True):
        # Brand Input Selection
        brand_source = st.radio("Brand Type:", ["Select Existing Brand", "Add New Brand"], horizontal=True)
        
        existing_brands = sorted(df['Brand'].astype(str).unique().tolist()) if not df.empty else []
        
        if brand_source == "Select Existing Brand" and existing_brands:
            new_brand = st.selectbox("Brand:", existing_brands)
        else:
            new_brand = st.text_input("New Brand Name (e.g., Hikvision):")
            
        new_model = st.text_input("Model / Series Name:")
        
        c1, c2 = st.columns(2)
        with c1: new_user = st.text_input("Default User:", value="admin")
        with c2: new_pass = st.text_input("Default Password:")
        
        new_info = st.text_area("Reset Instructions / Master Codes / Notes:", help="English is preferred for global reach.")
        
        # Submit Button
        submitted = st.form_submit_button("Save to Cloud Database 💾")
        
        if submitted:
            if new_brand and new_model:
                with st.spinner("Saving data to global server..."):
                    add_to_sheet(new_brand, new_model, new_user, new_pass, new_info)
                st.success(f"Success! {new_brand} - {new_model} has been added. Thank you for contributing!")
                st.experimental_rerun()
            else:
                st.error("Please fill in at least the Brand and Model fields.")

# Footer
st.markdown("---")
st.caption("🔒 Built for educational and professional maintenance purposes only.")
st.caption("Developed by the DVR Team Community.")
