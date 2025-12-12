import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json

# --- הגדרות חיבור לגוגל ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "DVR_DB"  # וודא שזה השם המדויק של הגיליון שלך בגוגל

def get_connection():
    """חיבור חכם - עובד גם מקומית וגם בענן"""
    try:
        # בדיקה 1: האם אנחנו בענן של Streamlit? (חיפוש בסודות)
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        
        # בדיקה 2: האם אנחנו במחשב בבית? (חיפוש קובץ json)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
            
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"שגיאת התחברות: {e}")
        st.stop()

def load_data():
    sheet = get_connection()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def add_to_sheet(brand, model, user, password, info):
    sheet = get_connection()
    sheet.append_row([brand, model, user, password, info])

# --- ממשק האפליקציה ---
st.set_page_config(page_title="DVR Team Cloud", page_icon="☁️", layout="centered")

st.title("☁️ DVR Passwords (Live)")
st.markdown("מערכת משותפת - זמינה 24/7")

# טעינת נתונים
try:
    df = load_data()
except Exception:
    df = pd.DataFrame(columns=["Brand", "Model", "User", "Pass", "Info"])

tab1, tab2 = st.tabs(["🔍 חיפוש", "➕ הוספה"])

# --- לשונית חיפוש ---
with tab1:
    if not df.empty:
        brands = sorted(df['Brand'].unique().tolist())
        selected_brand = st.selectbox("Brand:", brands)
        
        if selected_brand:
            models = sorted(df[df['Brand'] == selected_brand]['Model'].unique().tolist())
            selected_model = st.selectbox("Model:", models)
            
            if selected_model:
                # סינון ומציאת השורה
                row = df[(df['Brand'] == selected_brand) & (df['Model'] == selected_model)].iloc[0]
                
                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**User:** {row['User']}")
                with c2:
                    st.error(f"**Pass:** {row['Pass']}")
                
                st.warning(f"**Info:**\n{row['Info']}")
    else:
        st.info("המאגר ריק או לא נטען.")

# --- לשונית הוספה ---
with tab2:
    st.header("הוספת מכשיר")
    with st.form("add_form", clear_on_submit=True):
        brand_opt = st.radio("יצרן:", ["בחר קיים", "חדש"], horizontal=True)
        existing_brands = sorted(df['Brand'].unique().tolist()) if not df.empty else []
        
        if brand_opt == "בחר קיים" and existing_brands:
            new_brand = st.selectbox("בחר יצרן:", existing_brands)
        else:
            new_brand = st.text_input("שם יצרן חדש (באנגלית):")
            
        new_model = st.text_input("שם דגם:")
        c1, c2 = st.columns(2)
        with c1: new_user = st.text_input("User:", value="admin")
        with c2: new_pass = st.text_input("Password:")
        new_info = st.text_area("הוראות איפוס:")
        
        if st.form_submit_button("שמור לענן 💾"):
            if new_brand and new_model:
                with st.spinner("מעדכן..."):
                    add_to_sheet(new_brand, new_model, new_user, new_pass, new_info)
                st.success("עודכן בהצלחה!")
                st.rerun()
