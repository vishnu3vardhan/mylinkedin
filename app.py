import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time
from datetime import datetime
import re

# -------------------------------------
# 🔧 APP CONFIG
# -------------------------------------
st.set_page_config(
    page_title="Class LinkedIn Hub", 
    layout="centered",
    page_icon="🤝"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #0A66C2;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .profile-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #0A66C2;
    }
    .current-user {
        border-left: 4px solid #FFD700;
        background-color: #fffbf0;
    }
    .instructor-card {
        border-left: 4px solid #28a745;
        background-color: #f0fff4;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .refresh-indicator {
        text-align: center;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🤝 Class LinkedIn Hub</h1>', unsafe_allow_html=True)
st.caption("Search, add, and connect with your classmates instantly — auto-refresh available below!")

# Manual refresh button instead of auto-refresh
refresh_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f'<div class="refresh-indicator">🔄 Last updated: {refresh_time}</div>', unsafe_allow_html=True)

# -------------------------------------
# ⚙️ GOOGLE SHEETS SETUP
# -------------------------------------
SHEET_NAME = "myconnections"
WORKSHEET_INDEX = 0

@st.cache_resource(ttl=600)
def get_gspread_client():
    if "gcp_service_account" in st.secrets:
        sa_info = st.secrets["gcp_service_account"]
        sa_json = json.loads(sa_info) if isinstance(sa_info, str) else sa_info
        creds = Credentials.from_service_account_info(
            sa_json, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    else:
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
    return gspread.authorize(creds)

def validate_linkedin_username(username):
    """Validate LinkedIn username format"""
    username = username.strip()
    if not username:
        return False, "Username cannot be empty"
    
    # LinkedIn username pattern: alphanumeric, hyphens, underscores
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
        else:
            # Ensure required columns exist
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
    
    # Validate inputs
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
# 🔗 APP LOGIC
# -------------------------------------
try:
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).get_worksheet(WORKSHEET_INDEX)
    df = load_data(sheet)
except Exception as e:
    st.error(f"🚨 Connection Error: Unable to connect to Google Sheets. Please check your credentials.")
    st.stop()

# Initialize session state
if "current_username" not in st.session_state:
    st.session_state.current_username = None
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False

# Instructor setup
instructor_username = st.secrets.get("instructor_username", None)
if instructor_username and instructor_username not in df["username"].values:
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row(["Instructor", instructor_username, timestamp])
        df = load_data(sheet)
    except Exception as e:
        st.error(f"Error adding instructor: {str(e)}")

# -------------------------------------
# 📊 STATISTICS DASHBOARD
# -------------------------------------
st.subheader("📊 Class Statistics")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="stats-card"><h3>👥 Total Profiles</h3><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
with col2:
    unique_names = df["name"].nunique() if not df.empty else 0
    st.markdown(f'<div class="stats-card"><h3>🎯 Unique Members</h3><h2>{unique_names}</h2></div>', unsafe_allow_html=True)
with col3:
    recent_count = len(df)  # You could enhance this with actual timestamp filtering
    st.markdown(f'<div class="stats-card"><h3>🆕 Active</h3><h2>{recent_count}</h2></div>', unsafe_allow_html=True)

# -------------------------------------
# 🔍 SEARCH + ADD SECTION
# -------------------------------------
st.subheader("🔍 Search or Add Your LinkedIn")

with st.form("search_form"):
    search_username = st.text_input(
        "Enter your LinkedIn username (the part after linkedin.com/in/):",
        placeholder="e.g. john-doe-123",
        help="Only letters, numbers, hyphens, and underscores allowed"
    )
    
    submitted = st.form_submit_button("🔎 Search Profile")
    if submitted:
        st.session_state.search_performed = True
        if search_username:
            with st.spinner("Searching..."):
                time.sleep(0.5)  # Simulate processing
                match = df[df["username"].str.lower() == search_username.strip().lower()]
                if not match.empty:
                    name = match.iloc[0]["name"]
                    st.success(f"✅ Found! You are already listed as **{name}**.")
                    st.session_state.current_username = search_username.strip()
                else:
                    st.warning("❌ Not found in directory! Add yourself below 👇")
                    st.session_state.current_username = None
        else:
            st.error("Please enter a LinkedIn username to search")

# Show add form only if search was performed and no match found
if st.session_state.search_performed and search_username and st.session_state.current_username is None:
    with st.expander("➕ Add Me to Class Directory", expanded=True):
        with st.form("add_form"):
            name_input = st.text_input("Your full name:", placeholder="Enter your full name")
            agreed = st.checkbox("I confirm this is my correct LinkedIn username")
            
            submitted_add = st.form_submit_button("Add to Directory")
            if submitted_add:
                if not name_input:
                    st.error("Please enter your name.")
                elif not agreed:
                    st.error("Please confirm that the LinkedIn username is correct.")
                else:
                    with st.spinner("Adding to directory..."):
                        result, message = add_user(sheet, name_input, search_username)
                        if result == "added":
                            st.success(f"🎉 {message} Your profile will appear shortly.")
                            st.session_state.current_username = search_username.strip()
                            st.session_state.search_performed = False
                            # Refresh data
                            df = load_data(sheet)
                            st.rerun()
                        elif result == "exists":
                            st.info(f"ℹ️ {message}")
                        else:
                            st.error(f"❌ {message}")

st.divider()

# -------------------------------------
# 📘 CLASS DIRECTORY
# -------------------------------------
st.subheader(f"📘 Class Directory ({len(df)} members)")

# Manual refresh button at the top of directory
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh Directory"):
        df = load_data(sheet)
        st.success("Directory refreshed!")
        st.rerun()

# Sort instructor + current user first
display_df = df.copy()

if not display_df.empty:
    if instructor_username:
        instructor_mask = display_df["username"] == instructor_username
        instructor_rows = display_df[instructor_mask]
        other_rows = display_df[~instructor_mask]
        display_df = pd.concat([instructor_rows, other_rows])

    if st.session_state.current_username:
        current_mask = display_df["username"].str.lower() == st.session_state.current_username.lower()
        if current_mask.any():
            current_rows = display_df[current_mask]
            other_rows = display_df[~current_mask]
            display_df = pd.concat([current_rows, other_rows])

    # Display profiles
    for _, row in display_df.iterrows():
        name = row["name"]
        username = row["username"]
        url = f"https://www.linkedin.com/in/{username}/"
        
        card_class = "profile-card"
        if st.session_state.current_username and username.lower() == st.session_state.current_username.lower():
            card_class += " current-user"
            badge = "⭐ **YOU**"
        elif instructor_username and username == instructor_username:
            card_class += " instructor-card"
            badge = "🎓 **INSTRUCTOR**"
        else:
            badge = "👤"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}**")
                st.markdown(f"`@{username}`")
            with col2:
                st.markdown(badge)
            st.markdown(f"[🔗 Open LinkedIn Profile]({url})")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👋 No profiles yet. Be the first to add your LinkedIn profile!")

st.caption("📱 On mobile, LinkedIn links open directly in the LinkedIn app for quick connections!")

st.divider()

# -------------------------------------
# 🛠️ ADMIN SECTION (Collapsed by default)
# -------------------------------------
with st.expander("🛠️ Admin Tools", expanded=False):
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

# -------------------------------------
# 🌟 SOCIAL PROMO SECTION
# -------------------------------------
instagram_username = st.secrets.get("instagram_username", None)
if instagram_username:
    st.markdown(
        f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;'>
            <h4 style='margin: 0;'>💬 Follow the Creator</h4>
            <p style='margin: 0.5rem 0;'>Stay updated with more cool projects!</p>
            <a href='https://www.instagram.com/{instagram_username}/' target='_blank' 
               style='color: white; font-weight: bold; text-decoration: none; background: #E1306C; padding: 0.5rem 1rem; border-radius: 20px; display: inline-block;'>
               📸 Follow @{instagram_username}
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )

# -------------------------------------
# 📞 HELP SECTION
# -------------------------------------
with st.expander("❓ Need Help?", expanded=False):
    st.markdown("""
    **How to use this app:**
    1. 🔍 **Search**: Enter your LinkedIn username to check if you're in the directory
    2. ➕ **Add**: If not found, fill out the form to add yourself
    3. 📘 **Connect**: Browse classmates' profiles and connect on LinkedIn
    
    **What is a LinkedIn username?**
    - It's the part after `linkedin.com/in/` in your profile URL
    - Example: For `linkedin.com/in/john-doe-123`, your username is `john-doe-123`
    
    **Having issues?**
    - Make sure your username doesn't contain special characters
    - Check that you haven't already been added
    - Use the refresh button if data seems outdated
    - Contact your instructor if problems persist
    """)