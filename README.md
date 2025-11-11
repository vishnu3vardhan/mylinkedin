# mylinkedin
easy way connections

A Streamlit app that lets your entire class share and connect on LinkedIn — with live updates, profile counter, and your Instagram promo.

## Features
✅ Live update every 30 seconds  
✅ Shared Google Sheet storage  
✅ Search or add your LinkedIn username  
✅ Click names to open LinkedIn app  
✅ Profile counter  
✅ Instagram promo at bottom  

## Run locally
1. Put `service_account.json` in the project root.
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Deploy
- Push repo to GitHub.
- On Streamlit Cloud, add secrets:
  ```json
  {
    "gcp_service_account": { ... full JSON key ... },
    "instructor_username": "your-linkedin-username",
    "instagram_username": "your-instagram-username"
  }

