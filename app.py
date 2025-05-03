import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout='wide')

@st.cache_data
def load_data_for_instrument(instrument: str) -> pd.DataFrame:
    base = "https://raw.githubusercontent.com/TuckerArrants/sessions/main"
    fname = f"{instrument}_Session_Hits_Processed_from_2008.csv"
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
df['date'] = pd.to_datetime(df['session_date']).dt.date

# 1) Make sure 'date' is a datetime column
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["session_date"])
else:
    st.sidebar.warning("No 'date' column found in your data!")


# Sidebar

day_options = ['All'] + ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
selected_day = st.sidebar.selectbox("Day of Week", day_options)

min_date = df["date"].min().date()
max_date = df["date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
# 3) Filter your DataFrame
if isinstance(start_date, tuple):
    # sometimes date_input returns a single date if you pass a single default
    start_date, end_date = start_date

st.markdown("### Session High / Low Exclusion Filters")

row1_cols = st.columns([1, 1, 1, 1, 1, 1])
row2_cols = st.columns([1, 1, 1, 1, 1, 1])

with row1_cols[0]:
    prev_rdr_high_filter = st.multiselect(
        "Previous RDR High Touch",
        options=sorted(df["prev_rdr_high_touch_time_bucket"].dropna().unique().tolist())
    )
with row1_cols[1]:
    pre_adr_high_filter = st.multiselect(
        "Pre ADR High Touch",
        options=sorted(df["pre_adr_high_touch_time_bucket"].dropna().unique().tolist())
    )
with row1_cols[2]:
    adr_high_filter = st.multiselect(
        "ADR High Touch",
        options=sorted(df["adr_high_touch_time_bucket"].dropna().unique().tolist())
    )
with row1_cols[3]:
    adr_transition_high_filter = st.multiselect(
        "ADR Transition RDR High Touch",
        options=sorted(df["adr_transition_high_touch_time_bucket"].dropna().unique().tolist())
    )
with row1_cols[4]:
    odr_high_filter = st.multiselect(
        "ODR RDR High Touch",
        options=sorted(df["odr_high_touch_time_bucket"].dropna().unique().tolist())
    )
with row1_cols[5]:
    odr_transition_high_filter = st.multiselect(
        "ODR Transition RDR High Touch",
        options=sorted(df["odr_transition_high_touch_time_bucket"].dropna().unique().tolist())
    )

# Second Row
with row2_cols[0]:
    prev_rdr_low_filter = st.multiselect(
        "Previous RDR Low Touch",
        options=sorted(df["prev_rdr_low_touch_time_bucket"].dropna().unique().tolist())
    )
with row2_cols[1]:
    pre_adr_low_filter = st.multiselect(
        "Pre ADR Low Touch",
        options=sorted(df["pre_adr_low_touch_time_bucket"].dropna().unique().tolist())
    )
with row2_cols[2]:
    adr_low_filter = st.multiselect(
        "ADR Low Touch",
        options=sorted(df["adr_low_touch_time_bucket"].dropna().unique().tolist())
    )
with row2_cols[3]:
    adr_transition_low_filter = st.multiselect(
        "ADR Transition RDR Low Touch",
        options=sorted(df["adr_transition_low_touch_time_bucket"].dropna().unique().tolist())
    )
with row2_cols[4]:
    odr_low_filter = st.multiselect(
        "ODR RDR Low Touch",
        options=sorted(df["odr_low_touch_time_bucket"].dropna().unique().tolist())
    )
with row2_cols[5]:
    odr_transition_low_filter = st.multiselect(
        "ODR Transition Low High Touch",
        options=sorted(df["odr_transition_low_touch_time_bucket"].dropna().unique().tolist())
    )
