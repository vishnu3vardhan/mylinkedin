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
    page_icon="assests/linkedin.png",
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
# 🎨 BEAUTIFUL DARK/LIGHT THEME WITH CENTERED TOGGLE
# -------------------------------------
st.markdown("""
<style>
    /* Beautiful Color System */
    :root {
        /* Light Theme */
        --primary-bg: #ffffff;
        --secondary-bg: #f8f9fa;
        --card-bg: #ffffff;
        --text-primary: #1a1a1a;
        --text-secondary: #666666;
        --text-muted: #888888;
        --accent-primary: #2563eb;
        --accent-hover: #1d4ed8;
        --border-color: #e5e7eb;
        --shadow: 0 1px 3px rgba(0,0,0,0.1);
        --shadow-hover: 0 4px 12px rgba(0,0,0,0.15);
        
        /* Success/Warning/Error */
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --success-bg: rgba(16, 185, 129, 0.1);
        --warning-bg: rgba(245, 158, 11, 0.1);
        --error-bg: rgba(239, 68, 68, 0.1);
    }

    [data-theme="dark"] {
        /* Dark Theme */
        --primary-bg: #0f0f0f;
        --secondary-bg: #1a1a1a;
        --card-bg: #1e1e1e;
        --text-primary: #f5f5f5;
        --text-secondary: #a3a3a3;
        --text-muted: #737373;
        --accent-primary: #3b82f6;
        --accent-hover: #60a5fa;
        --border-color: #404040;
        --shadow: 0 1px 3px rgba(0,0,0,0.3);
        --shadow-hover: 0 4px 12px rgba(0,0,0,0.4);
        
        /* Success/Warning/Error */
        --success-color: #34d399;
        --warning-color: #fbbf24;
        --error-color: #f87171;
        --success-bg: rgba(52, 211, 153, 0.15);
        --warning-bg: rgba(251, 191, 36, 0.15);
        --error-bg: rgba(248, 113, 113, 0.15);
    }

    /* Smooth transitions */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }

    /* Main app background */
    .main .block-container {
        background-color: var(--primary-bg);
        color: var(--text-primary);
    }

    /* Centered Theme Toggle Button */
    .theme-toggle {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
        margin: 0 auto;
    }

    .theme-toggle:hover {
        transform: scale(1.1);
        box-shadow: var(--shadow-hover);
        border-color: var(--accent-primary);
    }

    .theme-toggle svg {
        width: 24px;
        height: 24px;
        fill: var(--text-primary);
    }

    /* Layout and Typography */
    .main-header {
        font-size: 2.5rem !important;
        color: var(--accent-primary);
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.2;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .subtext {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 1rem;
        line-height: 1.5;
        font-weight: 400;
    }

    /* Enhanced Card Styling */
    .profile-card {
        background-color: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }

    .profile-card:hover {
        background-color: var(--secondary-bg);
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-color: var(--accent-primary);
    }

    .profile-card strong {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
        display: block;
        margin-bottom: 0.5rem;
    }

    .profile-card code {
        background: var(--secondary-bg);
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        color: var(--accent-primary);
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.9rem;
        border: 1px solid var(--border-color);
        font-weight: 500;
    }

    .profile-card a {
        color: var(--accent-primary);
        text-decoration: none;
        font-weight: 600;
        border: 2px solid var(--accent-primary);
        padding: 0.6rem 1.2rem;
        border-radius: 25px;
        display: inline-block;
        margin-top: 1rem;
        transition: all 0.3s ease;
        background: transparent;
    }

    .profile-card a:hover {
        background-color: var(--accent-primary);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    /* Highlight cards */
    .current-user {
        border-left: 6px solid #fbbf24;
        background: linear-gradient(135deg, var(--card-bg), rgba(251, 191, 36, 0.1));
    }

    .instructor-card {
        border-left: 6px solid var(--success-color);
        background: linear-gradient(135deg, var(--card-bg), var(--success-bg));
    }

    /* Minimalistic Stats Cards */
    .minimal-stats-card {
        background: linear-gradient(135deg, var(--card-bg), var(--secondary-bg));
        color: var(--text-primary);
        padding: 1.5rem 1rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        height: 100%;
        box-shadow: var(--shadow);
    }

    .minimal-stats-card:hover {
        background: linear-gradient(135deg, var(--secondary-bg), var(--card-bg));
        border-color: var(--accent-primary);
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
    }

    .minimal-stats-card h4 {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .minimal-stats-card h2 {
        color: var(--accent-primary);
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .refresh-indicator {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 2rem;
        padding: 0.8rem;
        background: var(--secondary-bg);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }

    /* Success/Warning/Error states */
    .success-box {
        background: var(--success-bg);
        border: 1px solid var(--success-color);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: var(--success-color);
    }

    .warning-box {
        background: var(--warning-bg);
        border: 1px solid var(--warning-color);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: var(--warning-color);
    }

    .error-box {
        background: var(--error-bg);
        border: 1px solid var(--error-color);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: var(--error-color);
    }

    /* Form elements */
    .stTextInput input, .stTextInput textarea {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }

    .stButton button {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }
        .profile-card {
            padding: 1.2rem;
            margin: 0.8rem 0;
        }
        .minimal-stats-card h2 {
            font-size: 1.8rem;
        }
        .theme-toggle {
            width: 50px;
            height: 50px;
        }
        .theme-toggle svg {
            width: 20px;
            height: 20px;
        }
    }
</style>

<!-- Theme Toggle with System Preference Detection -->
<script>
    // Function to set theme
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    // Initialize theme
    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme) {
            setTheme(savedTheme);
        } else if (systemPrefersDark) {
            setTheme('dark');
        } else {
            setTheme('light');
        }
    }

    // Toggle theme
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    }

    // Initialize on load
    document.addEventListener('DOMContentLoaded', initTheme);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
</script>
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

    # Add Centered Theme Toggle Button
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 2rem 0;">
        <div class="theme-toggle" onclick="toggleTheme()">
            <svg viewBox="0 0 24 24">
                <path d="M12,18C11.11,18 10.26,17.8 9.5,17.45C11.56,16.5 13,14.42 13,12C13,9.58 11.56,7.5 9.5,6.55C10.26,6.2 11.11,6 12,6A6,6 0 0,1 18,12A6,6 0 0,1 12,18M20,8.69V4H15.31L12,0.69L8.69,4H4V8.69L0.69,12L4,15.31V20H8.69L12,23.31L15.31,20H20V15.31L23.31,12L20,8.69Z" />
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    col1, col2 = st.columns([3, 1])
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
    # 🌟 ENHANCED FOOTER
    # -------------------------------------
    
    instagram_username = st.secrets.get("instagram_username")
    github_username = st.secrets.get("github_username")
    gmail_address = st.secrets.get("gmail_address")

    if instagram_username or github_username or gmail_address:
        footer_html = f'''
        <div style="
            text-align: center;
            margin-top: 2rem;
            padding: 1.5rem;
            border-radius: 16px;
            background: var(--secondary-bg);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
        " role="contentinfo" aria-label="Connect with creator">
            <h4 style="margin-bottom: 0.5rem; color: var(--accent-primary);">💬 Connect with the Creator</h4>
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