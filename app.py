import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time
from datetime import datetime
import re
import os
import streamlit.components.v1 as components

# -------------------------------------
# ⚙️ APP CONFIG
# -------------------------------------
st.set_page_config(
    page_title="My Connections", 
    layout="centered",
    page_icon="assets/linkedin.png"
)

# -------------------------------
# 🎨 Minimalistic Styling
# -------------------------------
st.markdown("""
<style>
    /* Root theming */
    :root {
        --accent-color: #0A66C2;
        --text-primary: #111111;
        --text-secondary: #555555;
        --bg-card: #ffffff;
        --bg-hover: #f8f9fb;
    }
    [data-theme="dark"] {
        --accent-color: #60a5fa;
        --text-primary: #f5f5f5;
        --text-secondary: #cccccc;
        --bg-card: #1e1e1e;
        --bg-hover: #2a2a2a;
    }

    /* Layout and Typography */
    .main-header {
        font-size: 2.2rem !important;
        color: var(--accent-color);
        text-align: center;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    .subtext {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }

    /* Card Styling */
    .profile-card {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.6rem 0;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }
    .profile-card:hover {
        background-color: var(--bg-hover);
        transform: scale(1.01);
    }
    .profile-card strong {
        color: var(--text-primary);
        font-size: 1rem;
        text-transform: capitalize;
    }
    .profile-card code {
        background: rgba(0,0,0,0.1);
        padding: 0.2rem 0.4rem;
        border-radius: 6px;
        color: var(--text-primary);
    }
    [data-theme="dark"] .profile-card code {
        background: rgba(255,255,255,0.1);
        color: #b5f3ff;
    }
    .profile-card a {
        color: var(--accent-color);
        text-decoration: none;
        font-weight: 500;
    }
    .profile-card a:hover {
        text-decoration: underline;
    }

    /* Highlight cards */
    .current-user {
        border-left: 4px solid #FFD700;
        background-color: rgba(255, 215, 0, 0.08);
    }
    .instructor-card {
        border-left: 4px solid #2ecc71;
        background-color: rgba(46, 204, 113, 0.08);
    }

    /* Stats and Footer */
    .stats-card {
        background: var(--accent-color);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .refresh-indicator {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 🧭 Header Section
# -------------------------------
st.markdown('<h1 class="main-header"> 🔗 My Connections </h1>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Search, add, and connect with your classmates instantly.</div>', unsafe_allow_html=True)

refresh_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f'<div class="refresh-indicator">🔄 Last updated: {refresh_time}</div>', unsafe_allow_html=True)

# -------------------------------------
# 🧩 GOOGLE SHEETS SETUP
# -------------------------------------
SHEET_NAME = "myconnections"
WORKSHEET_INDEX = 0

@st.cache_resource(ttl=600)
def get_gspread_client():
    if "STREAMLIT_RUNTIME" in os.environ:
        sa_info = st.secrets["gcp_service_account"]
        sa_json = json.loads(sa_info) if isinstance(sa_info, str) else sa_info
        creds = Credentials.from_service_account_info(
            sa_json,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file",
            ],
        )
    else:
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file",
            ],
        )
    return gspread.authorize(creds)

# -------------------------------------
# 🔍 DATA HANDLING (Unchanged)
# -------------------------------------
def validate_linkedin_username(username):
    username = username.strip()

    # 🚫 Prevent spaces anywhere
    if " " in username:
        return False, "Username cannot contain spaces"

    if not username:
        return False, "Username cannot be empty"
    
    # Only letters, numbers, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\-_]+$'
    if not re.match(pattern, username):
        return False, "Invalid characters. Use only letters, numbers, hyphens, and underscores"
    
    if len(username) < 3:
        return False, "Username too short (min 3 characters)"
    
    if len(username) > 100:
        return False, "Username too long (max 100 characters)"
    
    return True, "Valid"


def load_data(sheet):
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=["name", "username", "timestamp"])
        if "timestamp" not in df.columns:
            df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df["name"] = df["name"].astype(str).str.strip()
        df["username"] = df["username"].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(columns=["name", "username", "timestamp"])

def add_user(sheet, name, username):
    username = username.strip()
    name = name.strip()
    if not name:
        return "invalid_name", "Please enter your name"
    is_valid, validation_msg = validate_linkedin_username(username)
    if not is_valid:
        return "invalid_username", validation_msg
    try:
        rows = sheet.get_all_records()
        for row in rows:
            if str(row.get("username", "")).lower() == username.lower():
                return "exists", "This username already exists in the directory"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, username, timestamp])
        return "added", "Successfully added to directory"
    except Exception as e:
        return "error", f"Error adding user: {str(e)}"

# -------------------------------------
# 🔗 MAIN LOGIC
# -------------------------------------
try:
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).get_worksheet(WORKSHEET_INDEX)
    df = load_data(sheet)
except Exception:
    st.error("🚨 Connection Error: Unable to connect to Google Sheets. Please check your credentials.")
    st.stop()

# -------------------------------------
# 📊 CLASS STATS
# -------------------------------------
st.subheader("Class Overview")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="stats-card"><h4> Total</h4><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stats-card"><h4> Unique</h4><h2>{df["name"].nunique() if not df.empty else 0}</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stats-card"><h4> Active</h4><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

st.divider()

# -------------------------------------
# 🔍 SEARCH / ADD SECTION
# -------------------------------------
st.subheader("🔍 Find or Add Your LinkedIn")

with st.form("search_form"):
    search_username = st.text_input("Your LinkedIn username:", placeholder="e.g. john-doe-123")
    submitted = st.form_submit_button("Search")
    if submitted:
        st.session_state.search_performed = True
        if search_username:
            with st.spinner("Searching..."):
                time.sleep(0.5)
                match = df[df["username"].str.lower() == search_username.strip().lower()]
                if not match.empty:
                    st.success(f"✅ Found! You are listed as **{match.iloc[0]['name']}**.")
                    st.session_state.current_username = search_username.strip()
                else:
                    st.warning("❌ Not found! Add yourself below ")
                    st.session_state.current_username = None
        else:
            st.error("Please enter a username to search")

if st.session_state.get("search_performed") and st.session_state.get("current_username") is None:
    with st.expander("➕ Add Me to Directory", expanded=True):
        with st.form("add_form"):
            name_input = st.text_input("Your full name:")
            agreed = st.checkbox("I confirm my LinkedIn username is correct")
            if st.form_submit_button("Add"):
                if not name_input:
                    st.error("Please enter your name.")
                elif not agreed:
                    st.error("Please confirm your username.")
                else:
                    with st.spinner("Adding..."):
                        result, message = add_user(sheet, name_input, search_username)
                        if result == "added":
                            st.success("Added successfully! Refreshing list...")
                            st.session_state.current_username = search_username
                            st.session_state.search_performed = False
                            st.rerun()
                        elif result == "exists":
                            st.info(message)
                        else:
                            st.error(message)

st.divider()

# -------------------------------------
# 📘 CLASS DIRECTORY
# -------------------------------------
st.subheader(f"🗳️ Class Directory ({len(df)} members)")
if st.button("🔄 Refresh Directory"):
    df = load_data(sheet)
    st.success("Directory refreshed!")
    st.rerun()

display_df = df.copy()

if not display_df.empty:
    for _, row in display_df.iterrows():
        name, username = row["name"], row["username"]
        url = f"https://www.linkedin.com/in/{username}/"
        card_class = "profile-card"
        badge = "👤"
        if st.session_state.get("current_username") and username.lower() == st.session_state["current_username"].lower():
            card_class += " current-user"
            badge = "⭐ YOU"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <strong>{name}</strong><br>
                    <code>@{username}</code>
                </div>
                <div>{badge}</div>
            </div>
            <a href="{url}" target="_blank">🔗 View LinkedIn Profile</a>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No profiles yet. Be the first to add yours!")

st.caption("📱 Tip: On mobile, links open directly in the LinkedIn app!")

st.divider()

# -------------------------------------
# 🛠️ ADMIN SECTION (Password Protected)
# -------------------------------------
with st.expander("🛠️ Admin Tools (Restricted Access)", expanded=False):
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    admin_password = st.secrets.get("admin_password", None)  # store this in secrets.toml

    if not st.session_state.admin_authenticated:
        password_input = st.text_input("Enter admin password:", type="password", key="admin_pass_input")
        if st.button("🔓 Unlock Admin Tools"):
            if password_input == admin_password:
                st.session_state.admin_authenticated = True
                st.success("✅ Access granted. Welcome, Admin!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    else:
        st.success("🔐 Admin access granted")

        st.write("**Data Management**")
        if st.button("🔄 Manual Refresh Data"):
            df = load_data(sheet)
            st.success("Data refreshed successfully!")
            st.rerun()

        st.write("**Export Data**")
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Directory as CSV",
                data=csv,
                file_name=f"class_linkedin_directory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

        st.write("**Debug Info**")
        st.code(f"Total records: {len(df)}")
        if not df.empty:
            st.code(f"Columns: {', '.join(df.columns)}")
            st.code(f"Sample data:\n{df.head(3).to_string()}")

        if st.button("🔒 Lock Admin Tools"):
            st.session_state.admin_authenticated = False
            st.info("Session locked. You will need to re-enter the password next time.")
            st.rerun()

# -------------------------------------
# 🌟 CONNECT WITH CREATOR (Footer)
# -------------------------------------
instagram_username = st.secrets.get("instagram_username", None)
github_username = st.secrets.get("github_username", None)
gmail_address = st.secrets.get("gmail_address", None)

if instagram_username or github_username or gmail_address:
    footer_html = f"""
    <div style="
        text-align: center;
        margin-top: 2rem;
        padding: 1.2rem;
        border-radius: 12px;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
    ">
        <h4 style="margin-bottom: 0.3rem; color: #0A66C2;">💬 Connect with the Creator</h4>
        <p style="margin-top: 0; margin-bottom: 0.8rem; color: #555;">
            Stay updated with more class tools & projects
        </p>
        <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
    """
    
    if instagram_username:
        footer_html += f"""
        <a href="https://www.instagram.com/{instagram_username}/" target="_blank"
           style="
               color: white;
               background: linear-gradient(90deg, #E1306C, #F77737);
               padding: 0.5rem 1.2rem;
               border-radius: 30px;
               font-weight: 600;
               text-decoration: none;
               display: inline-block;
           ">
           📸 @{instagram_username}
        </a>
        """
    
    if github_username:
        footer_html += f"""
        <a href="https://github.com/{github_username}" target="_blank"
           style="
               color: white;
               background: #24292E;
               padding: 0.5rem 1.2rem;
               border-radius: 30px;
               font-weight: 600;
               text-decoration: none;
               display: inline-block;
           ">
           💻 @{github_username}
        </a>
        """
    
    if gmail_address:
        footer_html += f"""
        <a href="mailto:{gmail_address}" target="_blank"
           style="
               color: white;
               background: #EA4335;
               padding: 0.5rem 1.2rem;
               border-radius: 30px;
               font-weight: 600;
               text-decoration: none;
               display: inline-block;
           ">
           📧 Gmail
        </a>
        """
    
    footer_html += "</div></div>"
    
    # Use components.html instead of st.markdown
    components.html(footer_html, height=200)