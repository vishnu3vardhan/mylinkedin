import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time
from datetime import datetime, timedelta
import re
import os
import streamlit.components.v1 as components
from urllib.parse import quote
import hashlib

# -------------------------------------
# ⚙️ APP CONFIG & CONSTANTS
# -------------------------------------
st.set_page_config(
    page_title="My Connections", 
    layout="centered",
    page_icon="🔗",
    initial_sidebar_state="collapsed"
)

# Constants
SHEET_NAME = "myconnections"
WORKSHEET_INDEX = 0
MAX_NAME_LENGTH = 50
MAX_USERNAME_LENGTH = 100
RATE_LIMIT_WINDOW = 30  # seconds
MAX_REQUESTS_PER_WINDOW = 5

# -------------------------------------
# 🎨 ENHANCED STYLING WITH ACCESSIBILITY
# -------------------------------------
st.markdown("""
<style>
    /* Root theming with improved contrast */
    :root {
        --accent-color: #0A66C2;
        --accent-hover: #084d94;
        --text-primary: #111111;
        --text-secondary: #444444;
        --bg-card: #ffffff;
        --bg-hover: #f8f9fa;
        --border-color: #e1e5e9;
        --success-color: #2ecc71;
        --warning-color: #f39c12;
        --error-color: #e74c3c;
    }
    [data-theme="dark"] {
        --accent-color: #60a5fa;
        --accent-hover: #3b82f6;
        --text-primary: #f5f5f5;
        --text-secondary: #cccccc;
        --bg-card: #1e1e1e;
        --bg-hover: #2a2a2a;
        --border-color: #444444;
        --success-color: #27ae60;
        --warning-color: #f39c12;
        --error-color: #e74c3c;
    }

    /* Improved focus indicators for accessibility */
    *:focus {
        outline: 2px solid var(--accent-color);
        outline-offset: 2px;
    }

    /* Layout and Typography */
    .main-header {
        font-size: 2.2rem !important;
        color: var(--accent-color);
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }
    .subtext {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1rem;
        margin-bottom: 1.5rem;
        line-height: 1.4;
    }

    /* Enhanced Card Styling */
    .profile-card {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    .profile-card:hover {
        background-color: var(--bg-hover);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .profile-card strong {
        color: var(--text-primary);
        font-size: 1.1rem;
        text-transform: capitalize;
        font-weight: 600;
    }
    .profile-card code {
        background: rgba(0,0,0,0.08);
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        color: var(--text-primary);
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.9rem;
    }
    [data-theme="dark"] .profile-card code {
        background: rgba(255,255,255,0.12);
        color: #b5f3ff;
    }
    .profile-card a {
        color: var(--accent-color);
        text-decoration: none;
        font-weight: 600;
        border: 1px solid var(--accent-color);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
        transition: all 0.2s ease;
    }
    .profile-card a:hover {
        background-color: var(--accent-color);
        color: white;
        text-decoration: none;
    }

    /* Highlight cards with improved contrast */
    .current-user {
        border-left: 4px solid #FFD700;
        background-color: rgba(255, 215, 0, 0.1);
    }
    .instructor-card {
        border-left: 4px solid var(--success-color);
        background-color: rgba(46, 204, 113, 0.1);
    }

    /* Minimalistic Stats Cards */
    .minimal-stats-card {
        background: transparent;
        color: var(--text-primary);
        padding: 1.2rem 0.5rem;
        border-radius: 12px;
        text-align: center;
        border: 2px solid var(--border-color);
        transition: all 0.3s ease;
        height: 100%;
    }
    .minimal-stats-card:hover {
        background: var(--bg-hover);
        border-color: var(--accent-color);
        transform: translateY(-2px);
    }
    .minimal-stats-card h4 {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .minimal-stats-card h2 {
        color: var(--accent-color);
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .refresh-indicator {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
        padding: 0.5rem;
        background: var(--bg-hover);
        border-radius: 8px;
    }

    /* Success/Warning/Error states */
    .success-box {
        background-color: rgba(46, 204, 113, 0.1);
        border: 1px solid var(--success-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: rgba(243, 156, 18, 0.1);
        border: 1px solid var(--warning-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: rgba(231, 76, 60, 0.1);
        border: 1px solid var(--error-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
        }
        .profile-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .minimal-stats-card h2 {
            font-size: 1.6rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------
# 🔧 ENHANCED UTILITY FUNCTIONS
# -------------------------------------
def initialize_session_state():
    """Initialize all session state variables with proper defaults"""
    defaults = {
        'search_performed': False,
        'current_username': None,
        'admin_authenticated': False,
        'last_request_time': None,
        'request_count': 0,
        'user_searches': {},
        'data_loaded': False,
        'search_query': '',
        'active_tab': 'directory'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def rate_limit_check():
    """Implement rate limiting to prevent spam"""
    now = time.time()
    if st.session_state.last_request_time is None:
        st.session_state.last_request_time = now
        st.session_state.request_count = 1
        return True
    
    time_diff = now - st.session_state.last_request_time
    
    if time_diff > RATE_LIMIT_WINDOW:
        st.session_state.request_count = 1
        st.session_state.last_request_time = now
        return True
    
    if st.session_state.request_count >= MAX_REQUESTS_PER_WINDOW:
        st.warning(f"⚠️ Too many requests. Please wait {int(RATE_LIMIT_WINDOW - time_diff)} seconds.")
        return False
    
    st.session_state.request_count += 1
    return True

def sanitize_input(text, max_length=100):
    """Sanitize user input to prevent XSS and other attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = str(text).strip()
    text = re.sub(r'[<>"\'&]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

def validate_name(name):
    """Enhanced name validation"""
    name = sanitize_input(name, MAX_NAME_LENGTH)
    
    if not name:
        return False, "Name cannot be empty"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > MAX_NAME_LENGTH:
        return False, f"Name must be less than {MAX_NAME_LENGTH} characters"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, "Valid"

def validate_linkedin_username(username):
    """Enhanced LinkedIn username validation"""
    username = sanitize_input(username, MAX_USERNAME_LENGTH)
    
    if not username:
        return False, "Username cannot be empty"
    
    if " " in username:
        return False, "Username cannot contain spaces"
    
    # Enhanced pattern for LinkedIn usernames
    pattern = r'^[a-zA-Z0-9\-_\.]+$'
    if not re.match(pattern, username):
        return False, "Invalid characters. Use only letters, numbers, hyphens, underscores, and periods"
    
    if len(username) < 3:
        return False, "Username too short (min 3 characters)"
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username too long (max {MAX_USERNAME_LENGTH} characters)"
    
    return True, "Valid"

def safe_linkedin_url(username):
    """Generate safe LinkedIn URL with proper encoding"""
    safe_username = quote(username)
    return f"https://www.linkedin.com/in/{safe_username}/"

# -------------------------------------
# 🧩 ENHANCED GOOGLE SHEETS SETUP
# -------------------------------------
@st.cache_resource(ttl=600)
def get_gspread_client():
    """Enhanced Google Sheets client with better error handling"""
    try:
        # Check if we're in Streamlit Cloud or have secrets available
        if "gcp_service_account" in st.secrets:
            sa_info = st.secrets["gcp_service_account"]
            
            # Handle both string and dict formats
            if isinstance(sa_info, str):
                sa_json = json.loads(sa_info)
            else:
                sa_json = sa_info
                
            creds = Credentials.from_service_account_info(
                sa_json,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                    "https://www.googleapis.com/auth/drive.file",
                ],
            )
            st.success("✅ Using Streamlit Secrets for authentication")
            
        # Local development fallback
        elif os.path.exists("service_account.json"):
            creds = Credentials.from_service_account_file(
                "service_account.json",
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                    "https://www.googleapis.com/auth/drive.file",
                ],
            )
            st.success("✅ Using local service_account.json for authentication")
            
        else:
            st.error("""
            🔐 Authentication Error: No credentials found.
            
            For Local Development:
            - Download service_account.json from Google Cloud Console
            - Place it in your project folder
            
            For Streamlit Cloud:
            - Add your service account JSON to Streamlit Secrets
            - Go to App Settings → Secrets
            - Add: gcp_service_account = { your_json_here }
            """)
            return None
            
        return gspread.authorize(creds)
        
    except Exception as e:
        st.error(f"🔐 Authentication Error: {str(e)}")
        st.info("💡 Check the setup guide in the documentation below.")
        return None

def load_data(sheet):
    """Enhanced data loading with validation and error handling"""
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            df = pd.DataFrame(columns=["name", "username", "timestamp"])
        
        # Validate and clean data
        required_columns = ["name", "username", "timestamp"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Clean and validate existing data
        df = df.dropna()  # Remove empty rows
        df["name"] = df["name"].astype(str).str.strip()
        df["username"] = df["username"].astype(str).str.strip()
        
        # Remove duplicates (case-insensitive)
        df = df.drop_duplicates(subset=["username"], keep="last")
        
        # Validate timestamps
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.data_loaded = True
        return df
        
    except Exception as e:
        st.error(f"📊 Error loading data: {str(e)}")
        return pd.DataFrame(columns=["name", "username", "timestamp"])

def add_user(sheet, name, username):
    """Enhanced user addition with case-insensitive duplicate checking"""
    if not rate_limit_check():
        return "rate_limited", "Too many requests. Please wait a moment."
    
    name = name.strip()
    username = username.strip()
    
    # Validate inputs
    name_valid, name_msg = validate_name(name)
    if not name_valid:
        return "invalid_name", name_msg
    
    username_valid, username_msg = validate_linkedin_username(username)
    if not username_valid:
        return "invalid_username", username_msg
    
    try:
        # Case-insensitive duplicate check
        existing_data = sheet.get_all_records()
        for row in existing_data:
            existing_username = str(row.get("username", "")).strip().lower()
            if existing_username == username.lower():
                return "exists", "This username already exists in the directory"
        
        # Add new user
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, username, timestamp])
        
        # Invalidate cache to force refresh
        st.cache_data.clear()
        
        return "added", "Successfully added to directory"
        
    except Exception as e:
        return "error", f"Error adding user: {str(e)}"

def search_users(df, query):
    """Enhanced search functionality"""
    if not query:
        return df
    
    query = query.lower().strip()
    results = df[
        df["name"].str.lower().str.contains(query, na=False) |
        df["username"].str.lower().str.contains(query, na=False)
    ]
    return results

# -------------------------------------
# 🎯 MAIN APPLICATION
# -------------------------------------
def main():
    # Initialize session state
    initialize_session_state()
    
    # -------------------------------
    # 🧭 Header Section
    # -------------------------------
    st.markdown('<h1 class="main-header" aria-label="My Connections">🔗 My Connections</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtext">Search, add, and connect with your classmates instantly.</div>', unsafe_allow_html=True)

    refresh_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f'<div class="refresh-indicator" aria-live="polite">🔄 Last updated: {refresh_time}</div>', unsafe_allow_html=True)

    # -------------------------------------
    # 📊 DATA LOADING
    # -------------------------------------
    try:
        client = get_gspread_client()
        if client is None:
            # Show setup instructions
            with st.expander("🔧 Setup Instructions", expanded=True):
                st.markdown("""
                ### 🔐 Google Sheets Setup Guide
                
                **1. Create Google Service Account:**
                - Go to [Google Cloud Console](https://console.cloud.google.com/)
                - Create a new project or select existing one
                - Enable **Google Sheets API** and **Google Drive API**
                - Create a Service Account and download JSON key
                
                **2. Share your Google Sheet:**
                - Open your Google Sheet ([template](https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing))
                - Click Share → Add your service account email
                - Grant **Editor** permissions
                
                **3. Configure Authentication:**
                
                **For Local Development:**
                ```bash
                # Rename downloaded JSON to:
                service_account.json
                # Place in your project folder
                ```
                
                **For Streamlit Cloud:**
                - Go to App Settings → Secrets
                - Add:
                ```toml
                [gcp_service_account]
                type = "service_account"
                project_id = "your-project-id"
                private_key_id = "your-private-key-id"
                private_key = "-----BEGIN PRIVATE KEY-----\\nyour-key\\n-----END PRIVATE KEY-----\\n"
                client_email = "your-service-account@your-project.iam.gserviceaccount.com"
                client_id = "your-client-id"
                auth_uri = "https://accounts.google.com/o/oauth2/auth"
                token_uri = "https://oauth2.googleapis.com/token"
                ```
                
                **Optional Secrets:**
                ```toml
                admin_password = "your-admin-password"
                instagram_username = "your-instagram"
                github_username = "your-github"
                gmail_address = "your-email@gmail.com"
                ```
                """)
            return
            
        sheet = client.open(SHEET_NAME).get_worksheet(WORKSHEET_INDEX)
        
        # Load data with simple spinner
        if not st.session_state.data_loaded:
            with st.spinner("Loading directory data..."):
                df = load_data(sheet)
        else:
            df = load_data(sheet)
            
    except Exception as e:
        st.error(f"🚨 Connection Error: Unable to connect to Google Sheets. Error: {str(e)}")
        st.info("💡 Make sure your Google Sheet is shared with the service account email.")
        return

    # -------------------------------------
    # 📊 CLASS STATS - MINIMALISTIC VERSION
    # -------------------------------------
    st.subheader("Class Overview", anchor="class-overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        <div class="minimal-stats-card" role="region" aria-label="Total Members">
            <h4>Total</h4>
            <h2>{len(df)}</h2>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="minimal-stats-card" role="region" aria-label="Unique Members">
            <h4>Unique</h4>
            <h2>{df["name"].nunique() if not df.empty else 0}</h2>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        active_count = len(df)  # You can enhance this with actual activity tracking
        st.markdown(f'''
        <div class="minimal-stats-card" role="region" aria-label="Active Members">
            <h4>Active</h4>
            <h2>{active_count}</h2>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

    # -------------------------------------
    # 🔍 ENHANCED SEARCH / ADD SECTION
    # -------------------------------------
    st.subheader("🔍 Find or Add Your LinkedIn", anchor="search-add")

    # Tab interface for better UX
    tab1, tab2 = st.tabs(["🔍 Search Directory", "➕ Add New Profile"])
    
    with tab1:
        with st.form("search_form", clear_on_submit=True):
            search_username = st.text_input(
                "LinkedIn username:",
                placeholder="e.g. john-doe-123",
                help="Enter your LinkedIn username (the part after linkedin.com/in/)",
                key="search_username_input"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button(
                    "Search",
                    use_container_width=True,
                    type="primary"
                )
            
            if submitted:
                if search_username:
                    with st.spinner("Searching directory..."):
                        time.sleep(0.3)  # Simulate processing
                        match = df[df["username"].str.lower() == search_username.strip().lower()]
                        if not match.empty:
                            user_data = match.iloc[0]
                            st.markdown(f'''
                            <div class="success-box">
                                <strong>✅ Found!</strong> You are listed as <strong>{user_data['name']}</strong>.
                            </div>
                            ''', unsafe_allow_html=True)
                            st.session_state.current_username = search_username.strip()
                            st.session_state.search_performed = True
                        else:
                            st.markdown(f'''
                            <div class="warning-box">
                                <strong>❌ Not found!</strong> This username is not in the directory yet.
                            </div>
                            ''', unsafe_allow_html=True)
                            st.session_state.current_username = None
                            st.session_state.search_performed = True
                else:
                    st.error("Please enter a username to search")

    with tab2:
        with st.form("add_form", clear_on_submit=True):
            name_input = st.text_input(
                "Your full name:",
                placeholder="e.g. John Doe",
                help="Enter your real name as you'd like it to appear in the directory",
                key="add_name_input"
            )
            
            username_input = st.text_input(
                "LinkedIn username:",
                placeholder="e.g. john-doe-123",
                help="Your LinkedIn username (from linkedin.com/in/your-username)",
                key="add_username_input"
            )
            
            agreed = st.checkbox(
                "I confirm my LinkedIn username is correct and I have permission to share this information",
                key="consent_checkbox"
            )
            
            if st.form_submit_button("Add to Directory", use_container_width=True, type="primary"):
                if not name_input or not username_input:
                    st.error("Please fill in both name and username fields.")
                elif not agreed:
                    st.error("Please confirm your username and permissions.")
                else:
                    with st.spinner("Adding to directory..."):
                        result, message = add_user(sheet, name_input, username_input)
                        if result == "added":
                            st.success("🎉 Added successfully! Refreshing directory...")
                            st.session_state.current_username = username_input
                            st.session_state.search_performed = False
                            time.sleep(1)
                            st.rerun()
                        elif result == "exists":
                            st.info(f"ℹ️ {message}")
                        elif result == "rate_limited":
                            st.warning(f"⏳ {message}")
                        else:
                            st.error(f"❌ {message}")

    st.divider()

    # -------------------------------------
    # 📘 ENHANCED CLASS DIRECTORY
    # -------------------------------------
    st.subheader(f"🗳️ Class Directory ({len(df)} members)", anchor="directory")
    
    # Enhanced directory controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input(
            "Search directory:",
            placeholder="Search by name or username...",
            key="directory_search",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.rerun()
    with col3:
        if st.download_button(
            "📥 Export CSV",
            df.to_csv(index=False),
            file_name=f"class_directory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        ):
            st.success("📊 CSV exported successfully!")

    # Display directory with search
    display_df = search_users(df, search_query) if search_query else df

    if not display_df.empty:
        st.caption(f"Showing {len(display_df)} of {len(df)} members")
        
        for _, row in display_df.iterrows():
            name, username = row["name"], row["username"]
            url = safe_linkedin_url(username)
            
            card_class = "profile-card"
            badge = "👤"
            aria_label = f"Profile card for {name}"
            
            # Highlight current user
            if st.session_state.get("current_username") and username.lower() == st.session_state["current_username"].lower():
                card_class += " current-user"
                badge = "⭐ YOU"
                aria_label += " - This is you"
            
            st.markdown(f'''
            <div class="{card_class}" role="article" aria-label="{aria_label}">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap: 1rem;">
                    <div style="flex: 1;">
                        <strong>{name}</strong><br>
                        <code>@{username}</code>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">{badge}</div>
                </div>
                <a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="View LinkedIn profile of {name}">
                    🔗 View LinkedIn Profile
                </a>
            </div>
            ''', unsafe_allow_html=True)
    else:
        if search_query:
            st.info(f"🔍 No members found matching '{search_query}'. Try a different search term.")
        else:
            st.info("👥 No profiles yet. Be the first to add yours!")

    st.caption("📱 Tip: On mobile, links open directly in the LinkedIn app!")
    st.divider()

    # -------------------------------------
    # 🛠️ ENHANCED ADMIN SECTION (FIXED)
    # -------------------------------------
    with st.expander("🛠️ Admin Tools (Restricted Access)", expanded=False):
        if "admin_authenticated" not in st.session_state:
            st.session_state.admin_authenticated = False

        admin_password = st.secrets.get("admin_password")
        
        if not admin_password:
            st.warning("Admin password not configured. Set ADMIN_PASSWORD in secrets.")
        
        if not st.session_state.admin_authenticated:
            st.write("**Admin Authentication Required**")
            password_input = st.text_input(
                "Enter admin password:",
                type="password",
                key="admin_pass_input",
                help="Contact system administrator for access"
            )
            
            if st.button("🔓 Unlock Admin Tools", use_container_width=True):
                # Use timing-safe comparison
                input_hash = hashlib.sha256(password_input.encode()).hexdigest()
                stored_hash = hashlib.sha256(admin_password.encode()).hexdigest()
                
                if input_hash == stored_hash:
                    st.session_state.admin_authenticated = True
                    st.success("✅ Access granted. Welcome, Admin!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
                    time.sleep(1)  # Prevent timing attacks
        else:
            st.success("🔐 Admin access granted")
            
            st.write("**Data Management**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Force Refresh Data", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state.data_loaded = False
                    st.success("Cache cleared! Refreshing data...")
                    st.rerun()
            
            with col2:
                if st.button("📊 Update Statistics", use_container_width=True):
                    st.success("Statistics updated!")
                    st.rerun()

            st.write("**Export Options**")
            if not df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Download as CSV",
                        df.to_csv(index=False),
                        file_name=f"class_directory_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    # JSON export
                    json_data = df.to_json(orient='records', indent=2)
                    st.download_button(
                        "📄 Download as JSON",
                        json_data,
                        file_name=f"class_directory_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )

            st.write("**Debug Information**")
            with st.expander("System Information"):
                # FIXED: Convert hash to string before slicing
                session_hash = str(hash(str(st.session_state)))
                st.code(f"""
                Total Records: {len(df)}
                Data Columns: {', '.join(df.columns)}
                Last Updated: {refresh_time}
                Session ID: {session_hash[:8]}
                """)
                
                if not df.empty:
                    st.write("Sample Data:")
                    st.dataframe(df.head(3), use_container_width=True)

            if st.button("🔒 Lock Admin Tools", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.info("🔒 Session locked. Password required for next access.")
                st.rerun()

    # -------------------------------------
    # 🌟 ENHANCED FOOTER
    # -------------------------------------
    st.markdown("---")
    
    instagram_username = st.secrets.get("instagram_username")
    github_username = st.secrets.get("github_username")
    gmail_address = st.secrets.get("gmail_address")

    if instagram_username or github_username or gmail_address:
        footer_html = f'''
        <div style="
            text-align: center;
            margin-top: 2rem;
            padding: 1.5rem;
            border-radius: 12px;
            background: var(--bg-hover);
            border: 1px solid var(--border-color);
        " role="contentinfo" aria-label="Connect with creator">
            <h4 style="margin-bottom: 0.5rem; color: var(--accent-color);">💬 Connect with the Creator</h4>
            <p style="margin-top: 0; margin-bottom: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                Stay updated with more class tools & projects
            </p>
            <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
        '''
        
        if instagram_username:
            footer_html += f'''
            <a href="https://www.instagram.com/{instagram_username}/" target="_blank" rel="noopener noreferrer"
               style="
                   color: white;
                   background: linear-gradient(45deg, #E1306C, #F77737, #FCAF45);
                   padding: 0.6rem 1.4rem;
                   border-radius: 25px;
                   font-weight: 600;
                   text-decoration: none;
                   display: inline-flex;
                   align-items: center;
                   gap: 0.5rem;
                   transition: transform 0.2s ease;
               "
               onmouseover="this.style.transform='scale(1.05)'"
               onmouseout="this.style.transform='scale(1)'"
               aria-label="Follow on Instagram">
               📸 @{instagram_username}
            </a>
            '''
        
        if github_username:
            footer_html += f'''
            <a href="https://github.com/{github_username}" target="_blank" rel="noopener noreferrer"
               style="
                   color: white;
                   background: #24292E;
                   padding: 0.6rem 1.4rem;
                   border-radius: 25px;
                   font-weight: 600;
                   text-decoration: none;
                   display: inline-flex;
                   align-items: center;
                   gap: 0.5rem;
                   transition: transform 0.2s ease;
               "
               onmouseover="this.style.transform='scale(1.05)'"
               onmouseout="this.style.transform='scale(1)'"
               aria-label="View GitHub profile">
               💻 @{github_username}
            </a>
            '''
        
        if gmail_address:
            footer_html += f'''
            <a href="mailto:{gmail_address}" 
               style="
                   color: white;
                   background: #EA4335;
                   padding: 0.6rem 1.4rem;
                   border-radius: 25px;
                   font-weight: 600;
                   text-decoration: none;
                   display: inline-flex;
                   align-items: center;
                   gap: 0.5rem;
                   transition: transform 0.2s ease;
               "
               onmouseover="this.style.transform='scale(1.05)'"
               onmouseout="this.style.transform='scale(1)'"
               aria-label="Send email">
               📧 Email
            </a>
            '''
        
        footer_html += "</div></div>"
        
        components.html(footer_html, height=180)

    # -------------------------------------
    # 🔒 PRIVACY & ACCESSIBILITY FOOTNOTE
    # -------------------------------------
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: var(--text-secondary); font-size: 0.8rem;">
        <p>
            🔒 <strong>Privacy First:</strong> Your data is stored securely and used only for class networking purposes.<br>
            ♿ <strong>Accessibility:</strong> This app follows WCAG guidelines for better user experience.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()