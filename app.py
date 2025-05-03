import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout='wide')

@st.cache_data
def load_data_for_instrument(instrument: str, period: str = "1H") -> pd.DataFrame:
    """
    Load the 1-minute quartal file for a single instrument.
    period must be "1H" or "3H".
    """ 
    base = "https://raw.githubusercontent.com/TuckerArrants/hourly_quarters/main"
    if period == "1H":
        fname = f"{instrument}_Sessions_1min_Processed_from_2008.csv"
    else:
        raise ValueError("period must be '1H' or '3H'")
    url = f"{base}/{fname}"
    try:
        return pd.read_csv(url)
    except Exception:
        # fallback to empty DF if file not found or network hiccup
        return pd.DataFrame()

# ↓ now pull exactly one file per timeframe:

# ✅ Store username-password pairs
USER_CREDENTIALS = {
    "badboyz": "bangbang",
    "dreamteam" : "strike",
}

# ✅ Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# ✅ Login form (only shown if not authenticated)
if not st.session_state["authenticated"]:
    st.title("Login to Database")

    # Username and password fields
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    # Submit button
    if st.button("Login"):
        if username in USER_CREDENTIALS and password == USER_CREDENTIALS[username]:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username  # Store the username
            # ← Clear *all* @st.cache_data caches here:
            st.cache_data.clear()

            st.success(f"Welcome, {username}! Loading fresh data…")
            st.rerun()
        else:
            st.error("Incorrect username or password. Please try again.")

    # Stop execution if user is not authenticated
    st.stop()

# ✅ If authenticated, show the full app
st.title("Sessions Database")

# ↓ in your sidebar:
instrument_options = ["ES", "NQ", "YM", "CL", "GC", "NG", "SI", "E6", "FDAX"]
selected_instrument = st.sidebar.selectbox("Instrument", instrument_options)

df = load_data_for_instrument(selected_instrument)
df['date'] = pd.to_datetime(df['time']).dt.date

# 1) Make sure 'date' is a datetime column
if "date" in df_1h.columns:
    df_1h["date"] = pd.to_datetime(df_1h["date"])
else:
    st.sidebar.warning("No 'date' column found in your data!")

# 2) Add a date‐range picker to the sidebar
