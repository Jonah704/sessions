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

# ✅ Store username-password pairs
USER_CREDENTIALS = {
    "badboyz": "bangbang",
    "dreamteam" : "strike",
}

segments = {
    "pre_adr":        (   0,  90),
    "adr":            (  90, 480),
    "adr_transition": ( 480, 540),
    "odr":            ( 540, 870),
    "odr_transition": ( 870, 930),
    "rdr":            ( 930,1380),
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
instrument_options = ["ES", "NQ", "YM", "CL", "GC", "NG", "HG", "SI", "E6", "FDAX"]
selected_instrument = st.sidebar.selectbox("Instrument", instrument_options)

df = load_data_for_instrument(selected_instrument)
df['date'] = pd.to_datetime(df['session_date']).dt.date

# 1) Make sure 'date' is a datetime column
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["session_date"])
else:
    st.sidebar.warning("No 'date' column found in your data!")


# SIDEBAR
day_options = ['All'] + ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
selected_day = st.sidebar.selectbox("Day of Week", day_options, key="selected_day")

min_date = df["date"].min().date()
max_date = df["date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_range"
)

# RESET BUTTON
default_filters = {
    "selected_day":               "All",
    "date_range":                 (min_date, max_date),
    "prev_rdr_high_filter":       ["all"], 
    "pre_adr_high_filter":        ["all"], 
    "adr_high_filter":            ["all"], 
    "adr_transition_high_filter": ["all"], 
    "odr_high_filter":            ["all"], 
    "odr_transition_high_filter": ["all"], 
    "prev_rdr_low_filter":        ["all"], 
    "pre_adr_low_filter":         ["all"], 
    "adr_low_filter":             ["all"], 
    "adr_transition_low_filter":  ["all"], 
    "odr_low_filter":             ["all"], 
    "odr_transition_low_filter":  ["all"], 
    "prev_rdr_high_filter_exclusion":       [], 
    "pre_adr_high_filter_exclusion":        [], 
    "adr_high_filter_exclusion":            [],
    "adr_transition_high_filter_exclusion": [],
    "odr_high_filter_exclusion":            [],
    "odr_transition_high_filter_exclusion": [], 
    "prev_rdr_low_filter_exclusion":        [],
    "pre_adr_low_filter_exclusion":         [],
    "adr_low_filter_exclusion":             [],
    "adr_transition_low_filter_exclusion":  [], 
    "odr_low_filter_exclusion":             [], 
    "odr_transition_low_filter_exclusion":  [],
}

# 2) Reset button with callback
def reset_all_filters():
    for key, default in default_filters.items():
        # only touch keys that actually exist
        if key in st.session_state:
            st.session_state[key] = default

st.sidebar.button("🔄 Reset all filters", on_click=reset_all_filters)

if isinstance(start_date, tuple):
    # sometimes date_input returns a single date if you pass a single default
    start_date, end_date = start_date

# FILTERS
st.markdown("### Session High / Low Inclusions")

segment_order = list(segments.keys())          # ["pre_adr","adr","adr_transition",…,"rdr"]
segment_order_with_no = segment_order + ["untouched"]

row1_cols = st.columns([1, 1, 1, 1, 1, 1])
row2_cols = st.columns([1, 1, 1, 1, 1, 1])

with row1_cols[0]:
    prev_rdr_high_filter = st.selectbox(
        "Previous RDR High Touch",
        options=["all"] + sorted(df["prev_rdr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="prev_rdr_high_filter"
    )
with row1_cols[1]:
    pre_adr_high_filter = st.selectbox(
        "Pre ADR High Touch",
        options=["all"] + sorted(df["pre_adr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="pre_adr_high_filter"
    )
with row1_cols[2]:
    adr_high_filter = st.selectbox(
        "ADR High Touch",
        options=["all"] + sorted(df["adr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_high_filter"
    )
with row1_cols[3]:
    adr_transition_high_filter = st.selectbox(
        "ADR Transition RDR High Touch",
        options=["all"] + sorted(df["adr_transition_high_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_transition_high_filter"
    )
with row1_cols[4]:
    odr_high_filter = st.selectbox(
        "ODR RDR High Touch",
        options=["all"] + sorted(df["odr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_high_filter"
    )
with row1_cols[5]:
    odr_transition_high_filter = st.selectbox(
        "ODR Transition RDR High Touch",
        options=["all"] + sorted(df["odr_transition_high_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_transition_high_filter"
    )

# Second Row
with row2_cols[0]:
    prev_rdr_low_filter = st.selectbox(
        "Previous RDR Low Touch",
        options=["all"] + sorted(df["prev_rdr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="prev_rdr_low_filter"
    )
with row2_cols[1]:
    pre_adr_low_filter = st.selectbox(
        "Pre ADR Low Touch",
        options=["all"] + sorted(df["pre_adr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="pre_adr_low_filter"
    )
with row2_cols[2]:
    adr_low_filter = st.selectbox(
        "ADR Low Touch",
        options=["all"] + sorted(df["adr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_low_filter"
    )
with row2_cols[3]:
    adr_transition_low_filter = st.selectbox(
        "ADR Transition RDR Low Touch",
        options=["all"] + sorted(df["adr_transition_low_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_transition_low_filter"
    )
with row2_cols[4]:
    odr_low_filter = st.selectbox(
        "ODR RDR Low Touch",
        options=["all"] + sorted(df["odr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_low_filter"
    )
with row2_cols[5]:
    odr_transition_low_filter = st.selectbox(
        "ODR Transition Low High Touch",
        options=["all"] + sorted(df["odr_transition_low_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_transition_low_filter"
    )

st.markdown("### Session High / Low Exclusions")

row3_cols = st.columns([1, 1, 1, 1, 1, 1])
row4_cols = st.columns([1, 1, 1, 1, 1, 1])

with row3_cols[0]:
    prev_rdr_high_filter_exclusion = st.multiselect(
        "Previous RDR High Touch",
        options=["none"] + sorted(df["prev_rdr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="prev_rdr_high_filter_exclusion"
    )
with row3_cols[1]:
    pre_adr_high_filter_exclusion = st.multiselect(
        "Pre ADR High Touch",
        options=["none"] + sorted(df["pre_adr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="pre_adr_high_filter_exclusion"
    )
with row3_cols[2]:
    adr_high_filter_exclusion = st.multiselect(
        "ADR High Touch",
        options=["none"] + sorted(df["adr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_high_filter_exclusion"
    )
with row3_cols[3]:
    adr_transition_high_filter_exclusion = st.multiselect(
        "ADR Transition RDR High Touch",
        options=["none"] + sorted(df["adr_transition_high_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_transition_high_filter_exclusion"
    )
with row3_cols[4]:
    odr_high_filter_exclusion = st.multiselect(
        "ODR RDR High Touch",
        options=["none"] + sorted(df["odr_high_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_high_filter_exclusion"
    )
with row3_cols[5]:
    odr_transition_high_filter_exclusion = st.multiselect(
        "ODR Transition RDR High Touch",
        options=["none"] + sorted(df["odr_transition_high_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_transition_high_filter_exclusion"
    )

# Second Row
with row4_cols[0]:
    prev_rdr_low_filter_exclusion = st.multiselect(
        "Previous RDR Low Touch",
        options=["none"] + sorted(df["prev_rdr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="prev_rdr_low_filter_exclusion"
    )
with row4_cols[1]:
    pre_adr_low_filter_exclusion = st.multiselect(
        "Pre ADR Low Touch",
        options=["none"] + sorted(df["pre_adr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="pre_adr_low_filter_exclusion"
    )
with row4_cols[2]:
    adr_low_filter_exclusion = st.multiselect(
        "ADR Low Touch",
        options=["none"] + sorted(df["adr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_low_filter_exclusion"
    )
with row4_cols[3]:
    adr_transition_low_filter_exclusion = st.multiselect(
        "ADR Transition RDR Low Touch",
        options=["none"] + sorted(df["adr_transition_low_touch_time_bucket"].dropna().unique().tolist()),
        key="adr_transition_low_filter_exclusion"
    )
with row4_cols[4]:
    odr_low_filter_exclusion = st.multiselect(
        "ODR RDR Low Touch",
        options=["none"] + sorted(df["odr_low_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_low_filter_exclusion"
    )
with row4_cols[5]:
    odr_transition_low_filter_exclusion = st.multiselect(
        "ODR Transition Low High Touch",
        options=["none"] + sorted(df["odr_transition_low_touch_time_bucket"].dropna().unique().tolist()),
        key="odr_transition_low_filter_exclusion"
    )
    
# Apply filters
st.markdown("### Distributions")

# map each filter to its column
inclusion_map = {
    "prev_rdr_high_touch_time_bucket": "prev_rdr_high_filter",
    "pre_adr_high_touch_time_bucket":  "pre_adr_high_filter",
    "adr_high_touch_time_bucket":      "adr_high_filter",
    "adr_transition_high_touch_time_bucket": "adr_transition_high_filter",
    "odr_high_touch_time_bucket":      "odr_high_filter",
    "odr_transition_high_touch_time_bucket": "odr_transition_high_filter",

    "prev_rdr_low_touch_time_bucket":  "prev_rdr_low_filter",
    "pre_adr_low_touch_time_bucket":   "pre_adr_low_filter",
    "adr_low_touch_time_bucket":       "adr_low_filter",
    "adr_transition_low_touch_time_bucket": "adr_transition_low_filter",
    "odr_low_touch_time_bucket":       "odr_low_filter",
    "odr_transition_low_touch_time_bucket": "odr_transition_low_filter",
}

exclusion_map = {
    "prev_rdr_high_touch_time_bucket": "prev_rdr_high_filter_exclusion",
    "pre_adr_high_touch_time_bucket":  "pre_adr_high_filter_exclusion",
    "adr_high_touch_time_bucket":      "adr_high_filter_exclusion",
    "adr_transition_high_touch_time_bucket": "adr_transition_high_filter_exclusion",
    "odr_high_touch_time_bucket":      "odr_high_filter_exclusion",
    "odr_transition_high_touch_time_bucket": "odr_transition_high_filter_exclusion",

    "prev_rdr_low_touch_time_bucket":  "prev_rdr_low_filter_exclusion",
    "pre_adr_low_touch_time_bucket":   "pre_adr_low_filter_exclusion",
    "adr_low_touch_time_bucket":       "adr_low_filter_exclusion",
    "adr_transition_low_touch_time_bucket": "adr_transition_low_filter_exclusion",
    "odr_low_touch_time_bucket":       "odr_low_filter_exclusion",
    "odr_transition_low_touch_time_bucket": "odr_transition_low_filter_exclusion",
}

# APPLY FILTERS
df_filtered = df.copy()

# — Day-of-week (shifted by +1 day) —
sel_day = st.session_state["selected_day"]
if sel_day != "All":
    df_filtered = df_filtered[
        (df_filtered["date"] + pd.Timedelta(days=1)).dt.day_name() == sel_day
    ]

# — Date range —
start_date, end_date = st.session_state["date_range"]
df_filtered = df_filtered[
    (df_filtered["date"] >= pd.to_datetime(start_date)) &
    (df_filtered["date"] <= pd.to_datetime(end_date))
]

for col, state_key in inclusion_map.items():
    sel = st.session_state[state_key]
    if sel != "All":
        df_filtered = df_filtered[df_filtered[col] == sel]

for col, state_key in exclusion_map.items():
    excludes = st.session_state[state_key]
    if excludes:
        df_filtered = df_filtered[~df_filtered[col].isin(excludes)]
        
# GRAPHS
df_plot = df.copy()

# HIGH touch‐time buckets
# HIGH touch‐time buckets
high_cols = [
    "prev_rdr_high_touch_time_bucket",
    "pre_adr_high_touch_time_bucket",
    "adr_high_touch_time_bucket",
    "adr_transition_high_touch_time_bucket",
    "odr_high_touch_time_bucket",
    "odr_transition_high_touch_time_bucket",
]
high_titles = [
    "Previous RDR High",
    "Pre-ADR High",
    "ADR High",
    "ADR-Transition High",
    "ODR High",
    "ODR-Transition High",
]

row1 = st.columns(6)
for idx, col in enumerate(high_cols):
    if col in df_filtered:
        counts = (
            df_filtered[col]
            .value_counts(normalize=True)
            .reindex(segment_order_with_no, fill_value=0)
        )
        perc = counts * 100

        fig = px.bar(
            x=perc.index,
            y=perc.values,
            text=[f"{v:.1f}%" for v in perc.values],
            labels={"x": "", "y": "% of Sessions"},
            title=high_titles[idx],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": segment_order_with_no},
            margin=dict(l=10, r=10, t=30, b=10),
        )

        row1[idx].plotly_chart(fig, use_container_width=True)


# LOW touch‐time buckets
low_cols = [
    "prev_rdr_low_touch_time_bucket",
    "pre_adr_low_touch_time_bucket",
    "adr_low_touch_time_bucket",
    "adr_transition_low_touch_time_bucket",
    "odr_low_touch_time_bucket",
    "odr_transition_low_touch_time_bucket",
]
low_titles = [
    "Previous RDR Low",
    "Pre-ADR Low",
    "ADR Low",
    "ADR-Transition Low",
    "ODR Low",
    "ODR-Transition Low",
]

row2 = st.columns(6)
for idx, col in enumerate(low_cols):
    if col in df_filtered:
        counts = (
            df_filtered[col]
            .value_counts(normalize=True)
            .reindex(segment_order_with_no, fill_value=0)
        )
        perc = counts * 100

        fig = px.bar(
            x=perc.index,
            y=perc.values,
            text=[f"{v:.1f}%" for v in perc.values],
            labels={"x": "", "y": "% of Sessions"},
            title=low_titles[idx],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": segment_order_with_no},
            margin=dict(l=10, r=10, t=30, b=10),
        )

        row2[idx].plotly_chart(fig, use_container_width=True)

st.caption(f"Sample size: {len(df_filtered):,} rows")
